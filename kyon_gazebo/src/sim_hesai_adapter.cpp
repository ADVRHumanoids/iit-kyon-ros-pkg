// gz gpu_lidar cloud -> Hesai QT128 driver cloud, so lio_mapping runs on it unchanged.
//  - Rings: each of the 128 rings takes the rendered row nearest to its elevation.
//  - Layout: one row of columns x 128 rings, ring fastest; x y z intensity (float32), ring
//    (uint16), timestamp (float64, s); no-returns as (0, 0, 0).
//  - Timing: clockwise sweep stamped at its start. gz renders the scan at once, taken as its end:
//    each column moves to the lidar pose at its own time (ground truth), i.e. motion distortion.

#include <nav_msgs/msg/odometry.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <sensor_msgs/msg/point_field.hpp>
#include <tf2/exceptions.h>
#include <tf2_eigen/tf2_eigen.hpp>
#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_listener.h>

#include <Eigen/Geometry>

#include <algorithm>
#include <cmath>
#include <cstring>
#include <deque>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

struct BasePose
{
    double t, x, y, z, yaw;
};

constexpr std::size_t kPointStep = 26;

sensor_msgs::msg::PointField field(const std::string& name, uint32_t offset, uint8_t type)
{
    sensor_msgs::msg::PointField f;
    f.name = name;
    f.offset = offset;
    f.datatype = type;
    f.count = 1;
    return f;
}

} // namespace

class SimHesaiAdapter : public rclcpp::Node
{
  public:
    SimHesaiAdapter()
      : rclcpp::Node("sim_hesai_adapter")
    {
        frame_id_ = declare_parameter<std::string>("frame_id", "hesai_lidar");
        base_frame_ = declare_parameter<std::string>("base_frame", "base_link");
        lidar_frame_ = declare_parameter<std::string>("lidar_parent_frame", "imu_link");
        const auto pose = declare_parameter<std::vector<double>>(
          "lidar_pose", std::vector<double>{0.0, 0.0, 0.0, 0.0, 0.0, 0.0});
        if (pose.size() != 6)
            throw std::invalid_argument("lidar_pose must be [x, y, z, roll, pitch, yaw]");
        lidar_in_parent_ = Eigen::Translation3d(pose[0], pose[1], pose[2]) *
                           Eigen::AngleAxisd(pose[5], Eigen::Vector3d::UnitZ()) *
                           Eigen::AngleAxisd(pose[4], Eigen::Vector3d::UnitY()) *
                           Eigen::AngleAxisd(pose[3], Eigen::Vector3d::UnitX());
        period_ = declare_parameter<double>("scan_period", 0.1);
        start_azimuth_ = declare_parameter<double>("start_azimuth_deg", 0.0) * M_PI / 180.0;
        rows_ = declare_parameter<int>("rows", 264);
        const double lo = declare_parameter<double>("min_elevation_deg", -52.8);
        const double hi = declare_parameter<double>("max_elevation_deg", 52.4);
        const auto rings =
          declare_parameter<std::vector<double>>("ring_elevations_deg", std::vector<double>{ 0.0 });
        double worst = 0.0;
        for (const double e : rings) {
            const int row = std::clamp(
              static_cast<int>(std::lround((e - lo) / (hi - lo) * (rows_ - 1))), 0, rows_ - 1);
            ring_rows_.push_back(row);
            worst = std::max(worst, std::abs(lo + row * (hi - lo) / (rows_ - 1) - e));
        }
        RCLCPP_INFO(get_logger(),
                    "%zu rings from %d rows, worst elevation error %.2f deg",
                    rings.size(),
                    rows_,
                    worst);

        tf_buffer_ = std::make_shared<tf2_ros::Buffer>(get_clock());
        tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);
        pub_ = create_publisher<sensor_msgs::msg::PointCloud2>(
          declare_parameter<std::string>("output_topic", "/lidar_points"), 5);
        gt_sub_ = create_subscription<nav_msgs::msg::Odometry>(
          declare_parameter<std::string>("ground_truth_topic", "/sim/ground_truth"),
          100,
          [this](nav_msgs::msg::Odometry::ConstSharedPtr msg) { onGroundTruth(*msg); });
        cloud_sub_ = create_subscription<sensor_msgs::msg::PointCloud2>(
          declare_parameter<std::string>("input_topic", "/hesai_qt128/points"),
          rclcpp::SensorDataQoS(),
          [this](sensor_msgs::msg::PointCloud2::ConstSharedPtr msg) { onCloud(*msg); });
    }

  private:
    void onGroundTruth(const nav_msgs::msg::Odometry& msg)
    {
        const auto& p = msg.pose.pose.position;
        const auto& q = msg.pose.pose.orientation;
        double yaw = std::atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z));
        // Continuous yaw, for interpolation.
        if (!trajectory_.empty())
            yaw = trajectory_.back().yaw + std::remainder(yaw - trajectory_.back().yaw, 2 * M_PI);
        trajectory_.push_back({ rclcpp::Time(msg.header.stamp).seconds(), p.x, p.y, p.z, yaw });
        while (trajectory_.size() > 400)
            trajectory_.pop_front();
    }

    // Base pose at t (level), interpolated; nullopt if the trajectory doesn't cover t.
    std::optional<Eigen::Isometry3d> basePose(double t) const
    {
        if (trajectory_.size() < 2 || t < trajectory_.front().t || t > trajectory_.back().t + 0.02)
            return std::nullopt;
        auto hi = std::lower_bound(trajectory_.begin(),
                                   trajectory_.end(),
                                   t,
                                   [](const BasePose& p, double v) { return p.t < v; });
        if (hi == trajectory_.end())
            hi = std::prev(trajectory_.end());
        if (hi == trajectory_.begin())
            hi = std::next(hi);
        const auto lo = std::prev(hi);
        const double s = std::clamp((t - lo->t) / std::max(hi->t - lo->t, 1e-9), 0.0, 1.0);
        const auto lerp = [s](double a, double b) { return a + s * (b - a); };
        Eigen::Isometry3d T = Eigen::Isometry3d::Identity();
        T.linear() = Eigen::AngleAxisd(lerp(lo->yaw, hi->yaw), Eigen::Vector3d::UnitZ()).matrix();
        T.translation() =
          Eigen::Vector3d(lerp(lo->x, hi->x), lerp(lo->y, hi->y), lerp(lo->z, hi->z));
        return T;
    }

    bool lookupLidar()
    {
        try {
            lidar_in_base_ = tf2::transformToEigen(tf_buffer_->lookupTransform(
                               base_frame_, lidar_frame_, tf2::TimePointZero)) *
                             lidar_in_parent_;
            return true;
        } catch (const tf2::TransformException& e) {
            RCLCPP_INFO_THROTTLE(get_logger(),
                                 *get_clock(),
                                 5000,
                                 "Waiting for %s -> %s: %s",
                                 base_frame_.c_str(),
                                 lidar_frame_.c_str(),
                                 e.what());
            return false;
        }
    }

    void onCloud(const sensor_msgs::msg::PointCloud2& msg)
    {
        if (!lidar_in_base_ && !lookupLidar())
            return;
        if (static_cast<int>(msg.height) != rows_) {
            RCLCPP_ERROR_THROTTLE(get_logger(),
                                  *get_clock(),
                                  5000,
                                  "Cloud has %u rows, expected %d (sim.yaml robot.lidar.rows)",
                                  msg.height,
                                  rows_);
            return;
        }
        int off_x = -1, off_y = -1, off_z = -1, off_i = -1;
        for (const auto& f : msg.fields) {
            if (f.datatype != sensor_msgs::msg::PointField::FLOAT32)
                continue;
            if (f.name == "x")
                off_x = f.offset;
            else if (f.name == "y")
                off_y = f.offset;
            else if (f.name == "z")
                off_z = f.offset;
            else if (f.name == "intensity")
                off_i = f.offset;
        }
        if (off_x < 0 || off_y < 0 || off_z < 0) {
            RCLCPP_ERROR_ONCE(get_logger(), "Cloud has no float32 x, y, z");
            return;
        }
        const double t_end = rclcpp::Time(msg.header.stamp).seconds();
        if (t_end < period_)
            return; // first scan of the sim: its sweep would start before time 0

        const int cols = msg.width;
        const std::size_t rings = ring_rows_.size();
        const double step = 2 * M_PI / cols;
        const double dt = period_ / cols;
        const auto base_end = basePose(t_end);
        if (!base_end)
            RCLCPP_WARN_THROTTLE(get_logger(),
                                 *get_clock(),
                                 5000,
                                 "No ground truth around this scan: published without motion "
                                 "distortion");
        const Eigen::Isometry3d lidar_end =
          base_end ? Eigen::Isometry3d(*base_end * *lidar_in_base_) : Eigen::Isometry3d::Identity();

        sensor_msgs::msg::PointCloud2 out;
        out.header.frame_id = frame_id_;
        const double t_start = t_end - period_ + dt;
        out.header.stamp = rclcpp::Time(static_cast<int64_t>(std::llround(t_start * 1e9)));
        out.height = 1;
        out.width = cols * rings;
        out.fields = { field("x", 0, sensor_msgs::msg::PointField::FLOAT32),
                       field("y", 4, sensor_msgs::msg::PointField::FLOAT32),
                       field("z", 8, sensor_msgs::msg::PointField::FLOAT32),
                       field("intensity", 12, sensor_msgs::msg::PointField::FLOAT32),
                       field("ring", 16, sensor_msgs::msg::PointField::UINT16),
                       field("timestamp", 18, sensor_msgs::msg::PointField::FLOAT64) };
        out.is_bigendian = false;
        out.point_step = kPointStep;
        out.row_step = kPointStep * out.width;
        out.is_dense = false;
        out.data.assign(out.row_step, 0);

        uint8_t* dst = out.data.data();
        for (int j = 0; j < cols; ++j) {
            // Sweep column j: azimuth start - j * step (clockwise); gz column c is at -pi + c *
            // step.
            const double az = start_azimuth_ - j * step;
            const int c =
              ((static_cast<int>(std::lround((az + M_PI) / step)) % cols) + cols) % cols;
            const double t = t_end - period_ + (j + 1) * dt;
            // Point seen at t_end, in the lidar frame at this column's time.
            Eigen::Isometry3d rel = Eigen::Isometry3d::Identity();
            if (base_end) {
                if (const auto base = basePose(t))
                    rel = (*base * *lidar_in_base_).inverse() * lidar_end;
            }
            for (std::size_t k = 0; k < rings; ++k, dst += kPointStep) {
                const uint8_t* src =
                  msg.data.data() + ring_rows_[k] * msg.row_step + c * msg.point_step;
                float x, y, z, intensity = 0.0f;
                std::memcpy(&x, src + off_x, 4);
                std::memcpy(&y, src + off_y, 4);
                std::memcpy(&z, src + off_z, 4);
                const uint16_t ring = static_cast<uint16_t>(k);
                std::memcpy(dst + 16, &ring, 2);
                std::memcpy(dst + 18, &t, 8);
                if (!std::isfinite(x) || !std::isfinite(y) || !std::isfinite(z))
                    continue; // no return: (0, 0, 0)
                if (off_i >= 0) {
                    std::memcpy(&intensity, src + off_i, 4);
                    intensity = std::clamp(intensity, 0.0f, 255.0f);
                }
                const Eigen::Vector3f p = (rel * Eigen::Vector3d(x, y, z)).cast<float>();
                std::memcpy(dst + 0, &p.x(), 4);
                std::memcpy(dst + 4, &p.y(), 4);
                std::memcpy(dst + 8, &p.z(), 4);
                std::memcpy(dst + 12, &intensity, 4);
            }
        }
        pub_->publish(out);
    }

    std::string frame_id_, base_frame_, lidar_frame_;
    double period_ = 0.1, start_azimuth_ = 0.0;
    int rows_ = 264;
    std::vector<int> ring_rows_;
    std::deque<BasePose> trajectory_;
    Eigen::Isometry3d lidar_in_parent_;
    std::optional<Eigen::Isometry3d> lidar_in_base_;

    std::shared_ptr<tf2_ros::Buffer> tf_buffer_;
    std::shared_ptr<tf2_ros::TransformListener> tf_listener_;
    rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_;
    rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr gt_sub_;
    rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr cloud_sub_;
};

int main(int argc, char** argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<SimHesaiAdapter>());
    rclcpp::shutdown();
    return 0;
}
