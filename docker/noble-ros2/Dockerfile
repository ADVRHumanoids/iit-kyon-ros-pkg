FROM hhcmhub/xbot2-noble-dev

SHELL ["/bin/bash", "-c"]

# Install headless display support
USER root
RUN apt-get update && apt-get install -y xvfb && rm -rf /var/lib/apt/lists/*

USER user
WORKDIR /home/user

# Pre-build all dependencies.
# This layer is cached in the registry and only rebuilt when this block changes.
RUN export HHCM_FOREST_CLONE_DEFAULT_PROTO=https && \
    mkdir -p ~/test_ws && cd ~/test_ws && \
    forest init && \
    source /opt/ros/jazzy/setup.bash && source setup.bash && \
    forest add-recipes https://github.com/advrhumanoids/multidof_recipes.git -t ros2 && \
    forest grow iit-kyon-ros-pkg --clone-depth 1 -j4 --tag-override hesai_jt128 && \
    forest grow xbot2_mujoco --clone-depth 1 -j4