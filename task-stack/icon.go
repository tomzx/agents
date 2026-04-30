package main

import (
	"bytes"
	"image"
	"image/color"
	"image/png"
	"math"

	"fyne.io/fyne/v2"
)

func makeIconPNG(hasTasks bool) []byte {
	const size = 64
	img := image.NewRGBA(image.Rect(0, 0, size, size))

	var c color.RGBA
	if hasTasks {
		c = color.RGBA{R: 59, G: 130, B: 246, A: 255}
	} else {
		c = color.RGBA{R: 156, G: 163, B: 175, A: 255}
	}

	cx, cy := float64(size)/2, float64(size)/2
	r := float64(size)/2 - 1

	for y := 0; y < size; y++ {
		for x := 0; x < size; x++ {
			dx := float64(x) - cx + 0.5
			dy := float64(y) - cy + 0.5
			if math.Sqrt(dx*dx+dy*dy) <= r {
				img.SetRGBA(x, y, c)
			}
		}
	}

	var buf bytes.Buffer
	_ = png.Encode(&buf, img)
	return buf.Bytes()
}

func makeIconFyne(hasTasks bool) fyne.Resource {
	return fyne.NewStaticResource("icon.png", makeIconPNG(hasTasks))
}
