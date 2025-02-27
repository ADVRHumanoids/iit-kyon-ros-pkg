#!/bin/bash

# Loop through all STL files in the current directory
for file in *.stl; do
    # Extract the filename without extension
    filename="${file%.*}"
    
    # Convert to DAE using assimp
    assimp export "$file" "./${filename}.dae"
    
    echo "Converted: $file -> ./${filename}.dae"
done

