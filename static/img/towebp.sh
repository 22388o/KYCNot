for i in *.jpeg; do
  cwebp -q 80 $i -o ${i%.*}.webp
done

