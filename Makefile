shutdown_systemctl:
	sudo systemctl stop icegridregistry
	sudo systemctl stop icegridnode
clean:
	rm -rf /tmp/db/node1
	rm -rf /tmp/db/registry
	rm -rf /tmp/db/distribution
stop:
	sudo systemctl stop icegridregistry
	sudo systemctl stop icegridnode
run:
	mkdir -p /tmp/db/node1
	mkdir -p /tmp/db/registry
	mkdir -p /tmp/db/distribution
	mkdir -p /tmp/db/node1/distrib/Downloader
	cp downloader.ice /tmp/db/distribution
	cp downloader.ice /tmp/db/node1/distrib/Downloader
	cp syncTimer.py /tmp/db/distribution
	cp syncTimer.py /tmp/db/node1/distrib/Downloader
	cp server.py /tmp/db/node1/distrib/Downloader
	cp server.py /tmp/db/distribution
	cp downloadScheduler.py /tmp/db/distribution
	cp downloadScheduler.py /tmp/db/node1/distrib/Downloader
	cp work_queue.py /tmp/db/distribution
	cp work_queue.py /tmp/db/node1/distrib/Downloader
	cp youtubedl.py /tmp/db/node1/distrib/Downloader
	chmod -R 777 /tmp/db/*

	icepatch2calc /tmp/db/distribution
	icegridnode --Ice.Config=node1.config
