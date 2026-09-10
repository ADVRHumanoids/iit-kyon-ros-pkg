FROM hhcmhub/xbot2-noble-dev

SHELL ["/bin/bash", "-c"]

# Install headless display support
USER root
RUN apt-get update && apt-get install -y xvfb nlohmann-json3-dev libglfw3-dev && rm -rf /var/lib/apt/lists/*

USER user
WORKDIR /home/user

# Pre-build all dependencies.
# This layer is cached in the registry and only rebuilt when this block changes.
# Credentials are injected via --secret and never stored in the image.
RUN source ~/env/bin/activate && \
    source /opt/xbot/setup.sh && \
    export HHCM_FOREST_CLONE_DEFAULT_PROTO=https && \
    git config --global url."https://x-access-token:${GH_TOKEN}@github.com/".insteadOf "https://github.com/" && \
    mkdir -p ~/test_ws && cd ~/test_ws && \
    forest init && \
    source /opt/ros/jazzy/setup.bash && source setup.bash && \
    forest add-recipes https://github.com/advrhumanoids/multidof_recipes.git -t kyon_refactor && \
    forest grow xbot2_mujoco -j4 && \
    forest grow iit-kyon-ros-pkg && \
    forest grow policy_deploy_toolkit && \
    cd ~/test_ws/src/iit-kyon-ros-pkg && git checkout refactor && cd ~/test_ws && forest grow iit-kyon-ros-pkg && \
    echo "source ~/test_ws/setup.bash" >> ~/.bashrc && echo "source /opt/xbot/setup.sh" >> ~/.bashrc