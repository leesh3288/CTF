from solver import exploit

base_ip = "10.13.37."

for i in range(1, 16):
  if i == 5:
    continue
  try:
    print(i)
    flag = exploit(base_ip + str(i), 5003)
    print("SUCCESS: " + flag)
  except:
    pass