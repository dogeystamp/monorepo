#!/bin/sh

while true
do
	RAND="$(seq 5 | shuf | head -n 1)"
	RET=""

	if [ "$RAND" = "1" ]
	then
		RET='init=/usr/sbin/reboot'
	else
		RET='noibrs noibpb nopti nospectre_v2 nospectre_v1 l1tf=off nospec_store_bypass_disable no_stf_barrier mds=off tsx=on tsx_async_abort=off mitigations=off'
	fi

	LEN=$(printf "$RET" | wc -c)

	HEADERS="HTTP/1.0 200 OK\r\nContent-Length: $LEN\r\n\r\n"

	RESP="$HEADERS$RET\r\n"

	printf "$RESP" \
	| nc -l -p 8080
done
