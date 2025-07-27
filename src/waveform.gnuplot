set terminal png size 2500,250;

set output 'waveform.png';
unset key;
unset tics;
unset border;
set lmargin 0;
set rmargin 0;
set tmargin 0;
set bmargin 0;

plot '<cat' binary filetype=bin format='%int16' endian=little array=1:0 with lines lc "black" lw 1;