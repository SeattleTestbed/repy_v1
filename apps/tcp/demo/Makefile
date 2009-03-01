# the dist 
REPYTAR=seattle_linux.tgz
# the untared dir
REPYDIR=seattle_repy

# Repy and Repypp
REPY=${REPYDIR}/repy.py 
REPYPP=${REPYDIR}/repypp.py 

# Tcp over upd lib
TCP=tcp.repy 

# the example scripts and restrictions file
TCUP=OurRepyTCPBenchmark#.repy
PYTCP=PythonTCPBenchmark#.py
REPYTCP=RepyTCPBenchmark#.repy 

RESTR=restrictions.default


# args 
PORT_A=12345 
PORT_B=12346
DESTIP=`hostname -i`
TOT=10000
CHUNK=100

DIST=tcpdemo

DEMO=demo

all: download demo

download: repy tcp benchmarks restrictions

demo: tcup pytcp repytcp 

# run it
tcuptest: download
	# Running TCUP Benchmark...
	python ${REPYPP} ${DEMO}.repy ${DEMO}
	python ${REPY} ${RESTR} ${DEMO} ${PORT_A} ${TOT} ${CHUNK}
        # done.
	#

tcup: download
	# Running TCUP Benchmark...
	python ${REPYPP} ${TCUP}.repy ${TCUP}
        # Arguments required: (-s or -c) LocalPort [DestinationIP DestinationPort TotalBytes ChunkSize]
	python ${REPY} ${RESTR} ${TCUP} -s ${PORT_B} &
	python ${REPY} ${RESTR} ${TCUP} -c ${PORT_A} ${DESTIP} ${PORT_B} ${TOT} ${CHUNK}
        # done.
	#

# run it
repytcp: download
	# Running Repy TCP Benchmark...
	python ${REPYPP} ${REPYTCP}.repy ${REPYTCP}
        # Arguments required: (-s or -c) LocalPort [DestinationIP DestinationPort TotalBytes ChunkSize]
	python ${REPY} ${RESTR} ${REPYTCP} -s ${PORT_B} &
	python ${REPY} ${RESTR} ${REPYTCP} -c ${PORT_A} ${DESTIP} ${PORT_B} ${TOT} ${CHUNK}
        # done.
	#

# run it
pytcp: download
	# Running Python TCP Benchmark...
        # Arguments required: (-s or -c) LocalPort [DestinationIP DestinationPort TotalBytes ChunkSize]
	python ${PYTCP}.py -s ${PORT_B} &
	python ${PYTCP}.py -c ${PORT_A} ${DESTIP} ${PORT_B} ${TOT} ${CHUNK}
        # done.
	#

semiclean:
	rm -rf ${TCUP}* ${REPYTCP}* ${PYTCP}* ${RESTR}

clean: semiclean
	rm -rf ${TCP} ${REPYDIR} ${REPYTAR} ${DIST} '.${DIST}' ${DIST}.tgz

superclean: clean
	killall -9 python


dist: clean
	mkdir '.${DIST}'
	cp * '.${DIST}'
	mv '.${DIST}' ${DIST}
	tar czf ${DIST}.tgz ${DIST}
	rm -rf ${DIST}

restrictions:
	cp ../tests/restrictions.default .

benchmarks:
	cp ../../../../benchmarks/tcp/*py .

# download repy
repy:
	# Dowloading Repy...
	if [ ! -e ${REPYDIR} ]; then wget --no-check-certificate https://seattlegeni.cs.washington.edu/geni/download/flibble/${REPYTAR}; tar xzf ${REPYTAR}; fi
	rm -f ${REPYTAR}
	# done.
	#

# download tcp/udp
tcp:
	# Dowloading TCP over UDP...
	if [ ! -e ${TCP} ]; then wget --no-check-certificate https://seattle.cs.washington.edu/raw-attachment/wiki/TopSecretReadme/${TCP}; fi
	# done.
	#
