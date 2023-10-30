### main ###
scale = 10
new_map = transform_map(gmap, pixels = scale)

lpt = Point(220, 220)
upt = Point(150,168)

tf_lpt = transform_point(lpt, scale=scale)
tf_upt = transform_point(upt,  scale=scale)

x_init = tf_lpt.x
y_init = tf_lpt.y
width =  tf_lpt.x  - tf_upt.x + 1
inc = 2
