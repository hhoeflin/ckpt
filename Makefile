MAKEFILE_DIR=$(realpath $(dir $(firstword $(MAKEFILE_LIST))))

CONDA_ENV:=${MAKEFILE_DIR}/.conda_env
REPO_NAME:=checkpoint

# ENVIRONMENT
create-base-env:
	conda env create --prefix ${CONDA_ENV} --file conda_env.yaml \
	&& conda run --prefix ${CONDA_ENV} flit install -s

lock-env:
	conda env export --prefix ${CONDA_ENV} | grep -v ${REPO_NAME} > conda_env.lock.yaml

create-lock-env:
	conda env create --prefix ${CONDA_ENV} --file conda_env.lock.yaml \
	&& conda run --prefix ${CONDA_ENV} flit install -s
