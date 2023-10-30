### main ###
scale = 10
new_map = transform_map(gmap, pixels = scale)

lpt = Point(220, 220)
upt = Point(150,168)

tf_lpt = transform_point(lpt, scale=scale)
tf_upt = transform_point(upt,  scale=scale)
