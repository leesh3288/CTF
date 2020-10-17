from subprocess import run, PIPE

TARGET = "./target"

fin = open(TARGET, "rb")
c = fin.read()
fin.close()

fout= open("enc.bin", "wb")
for i in range((len(c) + 7) // 8):
    d = c[8*i:8*i+8]
    p = run(['input'], stdout=PIPE, input=d)
    fout.write(p.stdout.strip())
fout.close()