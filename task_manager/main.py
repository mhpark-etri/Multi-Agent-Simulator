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

### full coverage path ###
goal_list = []
for y_cnt in range(0, width, inc):
  if y_cnt % 2==0: x_init = tf_lpt.x
  else: x_init = tf_lpt.x - width + 1

  for x_cnt in range(0, width, inc):
    if y_cnt % 2==0: x = x_init - x_cnt
    else: x = x_init +x_cnt
    y= y_init - y_cnt
    goal_list.append((x,y)) 
