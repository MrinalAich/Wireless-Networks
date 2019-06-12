set terminal png
set output "Throughput.png" 
set title "Throughput-Flows plot"
set xlabel "No. of Flows" 
set ylabel "Throughput (Mbps)"

plot "throughput_dataSet.txt" using 1:2 with lines title "UL w/o RTS-CTS", \
     "throughput_dataSet.txt" using 1:3 with lines title "UL RTS-CTS", \
     "throughput_dataSet.txt" using 1:4 with lines title "DL w/o RTS-CTS", \
     "throughput_dataSet.txt" using 1:5 with lines title "DL RTS-CTS"