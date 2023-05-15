NAME:=ffp-xmlcollect-receiver
VOLUMES:=-v ${CURDIR}/tmpstor/:/tmpstor/
PORT:=17485
RECVTHREADS:=128
NET:=ffp
RESTART:=unless-stopped
RUNARGS:=--ip6 "2a03:4000:5e:f7f:ff::444d" --memory=2g

CID=`docker ps | grep ${NAME} | cut -d' ' -f1`
ENV=-e "GIT_COMMIT=`git rev-parse HEAD`" -e "HOSTHOSTNAME=`hostname`" -e "UID=`id -u`" -e "GID=`id -g`" \
	-e "TMPSTOR=/tmpstor/" -e "PORT=${PORT}" -e "RECVTHREADS=${RECVTHREADS}" 

build:
	docker build -t ${NAME} . || docker build --no-cache -t ${NAME} .
.PHONY: build

run: stop remove build
	docker run -d --restart ${RESTART} --name ${NAME} --network ${NET} ${ENV} ${VOLUMES} ${RUNARGS} ${NAME}
.PHONY: run

shell: running
	docker exec -it "${CID}" bash
.PHONY: shell

stop:
	-docker stop "${CID}"
.PHONY: stop

remove:
	-docker container rm "${NAME}"
.PHONY: stop

log: running
	docker attach --sig-proxy=false "${CID}"
.PHONY: log

runlog: run log
.PHONY: runlog

running:
	test "${CID}" != "" || ( echo -e "Docker container is not running." ; exit 1 )

.PHONY: running
clean: stop
.PHONY: clean


