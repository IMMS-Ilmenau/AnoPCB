uploadall: buildall
	docker tag anopcb-server:cpu julian20delta/anopcb-server:cpu
	docker push julian20delta/anopcb-server:cpu
	docker tag anopcb-server:gpu julian20delta/anopcb-server:gpu
	docker push julian20delta/anopcb-server:gpu

.PHONY: uploadall buildall buildgpu buildcpu dependincies

buildall: buildgpu buildcpu

buildgpu: dependincies
	docker build --build-arg TENSORFLOW_ARG_TAGS=-gpu --tag anopcb-server:gpu .

buildcpu: dependincies
	docker build --tag anopcb-server:cpu .

dependincies: pip_requirements_docker.txt Dockerfile AnomalyServer.py