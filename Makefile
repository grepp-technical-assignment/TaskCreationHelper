build:
	docker build -t tch:1.1 ./

test:
	docker run --name TCH -v $(PWD):/TCH/VOLUME -it --rm tch:1.1 run.py -l full -c VOLUME/Examples/SortTheList/