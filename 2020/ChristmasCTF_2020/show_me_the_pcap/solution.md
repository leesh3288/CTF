1. Extract rtpdump & .sdp from pcap using wireshark (Telephony -> RTP -> RTP Streams)
   ```
   v=0
   c=IN IP4 127.0.0.1
   a=tool:libavformat 57.83.100 
   m=video 43434 RTP/AVP 96
   b=AS:200 
   a=rtpmap:96 MP4V-ES/90000 
   a=fmtp:96 profile-level-id=1; config=000001B001000001B58913000001000000012000C48D8DC43D3C04871443000001B24C61766335372E3130372E313030 
   a=control:streamid=0 
   ```
2. Use ffmpeg to load the .sdp & listen to localhost/43434
3. rtpplay to localhost/43434: `rtpplay -Tv -f file.rtpdump localhost/43434`
4. Listen using ffmpeg: `ffmpeg -protocol_whitelist "file,rtp,udp" -i file.sdp -t 5 file.mp4`

FLAG: `XMAS{Kiss-me-Thru-the-RTP}`