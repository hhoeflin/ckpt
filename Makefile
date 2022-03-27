MAKEFILE_DIR:=$(realpath $(dir $(firstword $(MAKEFILE_LIST))))

create-env:
	conda create -y --prefix ${MAKEFILE_DIR}/conda_env python=3.8 \
		&& conda install --prefix ${MAKEFILE_DIR}/conda_env poetry \
		&& conda run -y --prefix ${MAKEFILE_DIR}/conda_env poetry install
