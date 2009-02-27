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
TOT=1000
CHUNK=10

DIST=tcpdemo

all: download demo

download: repy tcp benchmarks restrictions

demo: pytcp repytcp tcup

# run it
tcup:
	# Running TCUP Benchmark...
	python ${REPYPP} ${TCUP}.repy ${TCUP}
        # Arguments required: (-s or -c) LocalPort [DestinationIP DestinationPort TotalBytes ChunkSize]
	python ${REPY} ${RESTR} ${TCUP} -s ${PORT_B} &
	python ${REPY} ${RESTR} ${TCUP} -c ${PORT_A} ${DESTIP} ${PORT_B} ${TOT} ${CHUNK}
        # done.
	#

# run it
repytcp:
	# Running Repy TCP Benchmark...
	python ${REPYPP} ${REPYTCP}.repy ${REPYTCP}
        # Arguments required: (-s or -c) LocalPort [DestinationIP DestinationPort TotalBytes ChunkSize]
	python ${REPY} ${RESTR} ${REPYTCP} -s ${PORT_B} &
	python ${REPY} ${RESTR} ${REPYTCP} -c ${PORT_A} ${DESTIP} ${PORT_B} ${TOT} ${CHUNK}
        # done.
	#

# run it
pytcp:
	# Running Python TCP Benchmark...
        # Arguments required: (-s or -c) LocalPort [DestinationIP DestinationPort TotalBytes ChunkSize]
	python ${PYTCP}.py -s ${PORT_B} &
	python ${PYTCP}.py -c ${PORT_A} ${DESTIP} ${PORT_B} ${TOT} ${CHUNK}
        # done.
	#

semiclean:
	rm -rf ${TCUP}* ${REPYTCP}* ${PYTCP}* ${RESTR}

clean:
	rm -rf ${TCP} ${REPYDIR} ${REPYTAR} ${TCUP}* ${REPYTCP}* ${PYTCP}* ${DIST} '.${DIST}' ${DIST}.tgz

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
	if [ ! -e ${REPYDIR} ]; then wget https://seattlegeni.cs.washington.edu/geni/download/flibble/${REPYTAR}; tar xzf ${REPYTAR}; fi
	rm -f ${REPYTAR}
	# done.
	#

# download tcp/udp
tcp:
	# Dowloading TCP over UDP...
	if [ ! -e ${TCP} ]; then wget https://seattle.cs.washington.edu/raw-attachment/wiki/TopSecretReadme/${TCP}; fi
	# done.
	#
