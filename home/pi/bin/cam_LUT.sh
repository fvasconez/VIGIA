#!/bin/bash

# LUT script: for any value of ISO speed, shutter speed or aperture, find the right value
# that the camera Canon EOS 4000D accepts

# @author fvasconez
# @created 2022.05.05

# The tables MUST be in decreasing order
ISO_speed=(
6400
3200
1600
800
400
200
100
0
)

ShutterSP=(
30
25
20
15
13
10
8
6
5
4
3.2
2.5
2
1.6
1.3
1
0.8
0.6
0.5
0.4
0.3
1/4
1/5
1/6
1/8
1/10
1/13
1/15
1/20
1/25
1/30
1/40
1/50
1/60
1/80
1/100
1/125
1/160
1/200
1/250
1/320
1/400
1/500
1/640
1/800
1/1000
1/1250
1/1600
1/2000
1/2500
1/3200
1/4000
)

Aperture=(
36
32
29
25
22
20
18
16
14
13
11
10
9
8
7.1
6.3
5.6
5
4.5
)

if (( $# < 2 )); then
    echo "Error using LUT:"
    echo "   cam_LUT.sh (iso|shutter|aperture) <value>"
    exit 1
else
    if [[ $1 == "iso" ]]; then
        LUT=(${ISO_speed[@]})
    elif [[ $1 == "shutter" ]]; then
        LUT=(${ShutterSP[@]})
    elif [[ $1 == "aperture" ]]; then
        LUT=(${Aperture[@]})
    else
        echo "Error using LUT:"
        echo "   cam_LUT.sh (iso|shutter|aperture) <value>"
        exit 1
    fi
    in_val=$2
fi

last=${LUT[0]}
len=$((${#LUT[@]}-1))


if (( $(echo "scale=5; $in_val < $last" | bc) )) ; then   #in_val is not greater than lut values
    if (( $(echo "scale=5; $in_val > ${LUT[len]}" | bc) )) ; then 
    # check each value, starting at the second position
        for lut_val in ${LUT[@]:1:len} ; do
            if (( $(echo "scale=5; $in_val < $lut_val" | bc) )); then
                last=$lut_val
            elif (( $(echo "$(echo "scale=5; $last - $in_val"|bc) > $(echo "scale=5; $in_val - $lut_val"|bc)" | bc) )) ; then
                out_val=$lut_val
                break
            else
                out_val=$last
                break
            fi
        done
    else    #in_val is out of range, too short
        out_val=${LUT[len]}
    fi
else    #in_val is out of range, too big
    out_val=$last
fi

echo "$out_val"
