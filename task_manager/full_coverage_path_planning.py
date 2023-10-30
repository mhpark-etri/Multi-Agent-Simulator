### naive full coverage path planning algorithm
def naive_path_planning(x_init, y_init, tf_lpt, width, inc, gmap):
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
  return glist2
