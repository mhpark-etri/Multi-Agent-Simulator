import area_split

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

goal_list = np.array(goal_list)*scale
goal_list2 = goal_list.copy()
for idx, (i,j) in enumerate(goal_list):
  if gmap[i,j] < 240:
    for di in range(i-10, i+10):
      di = max(di, 0)
      for dj in range(j-10, j+10):
        dj = max(dj, 0)
        if gmap[di,dj]>=240: 
          goal_list2[idx, :] = [di, dj]
          break
      if gmap[di,dj]>=240: break
    print(i,j, di, dj, gmap[i,j],  gmap[di,dj])

plt.imshow(gmap, cmap='gray')
plt.scatter(y=goal_list2[:,0], x=goal_list2[:,1])
plt.show()
