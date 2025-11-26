#/bin/env bash

PICS_DIR=~/test_pics				# Replace to your temp directory
UPLOAD_URL='_your_upload_url_'

echo Pictures will be sent to $UPLOAD_URL

while [ 0 ]; do

    for f in $PICS_DIR/*.jpg; do
        if [ -f $f ]; then
            curl -H 'Content-Type: image/jpeg' --data-binary @$f $UPLOAD_URL > /dev/null
            rm $f
        fi
    done

    sleep 0.5
done
