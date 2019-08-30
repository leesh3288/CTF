DEF CON CTF 27 Review
=====================

DEF CON CTF 27 was my second time in an on-site CTF competition, and the first time trying an Attack-and-Defense style competition. Our team **KaisHack GoN** arrived at Las Vegas two days before the CTF. We had some hard time setting up network and stuff (our server had no WLAN support, which was necessary to open a VPN server to the network) but eventually managed to sort out things in a sub-usable state.

This review is grouped largely into three parts. The first is about how I've approached the challenges and what I've done to solve them. The second is roughly about what was good about the challenges and what I felt that could have been better. The last is an analysis of my performance throughout the CTF, what my mistakes were and what could have been better.

---

## Day 1

The CTF started with two challenges, `ropship` (KotH) and `telooogram` (A&D) in which I decided to put my effort in the former. `ropship` in a single sentence is to "control a ship with ROP chain". The chal asks us to supply a x64 machine code that generates a ROP chain in a 500,000,000 bytes sized randomly genererated executable section. Then a runner stub sets its stack pointer to the ROP chain, which then should set a certain memory to either `u, d, l, r, a, s, n` where each character is the action of the ship to accelerate up/down/left/right, attack, shield, or do no operation. Since there is cooltime in attack and shield, we are required to use them wisely (especially the shield). While running the ROP chain, the program is able to see the game state, which are game tick, all ships' score/shield status/location/direction/speed, and all bullets' location/direction.

Since the code that we can use for ROPing is randomly generated, it is almost guaranteed that any 3 byte ROP gadget (2 byte instruction + ret) exists, but 4 byte gadget (3 byte inst + ret) probably would not exist. If we absolutely must use a 4 byte ROP gadget, we can try checking for all the registers that the gadget uses. I initially focused on generating a ROP chain that reads the map state and initiates a dogfight with the closest enemy, which I thought is the best possible fighting strategy available. Real warplanes do that, so why not do it in the game?

Well, it turns out that other players started with very basic strategies, such as rotating & shooting in their initial position, or rotating in circles & shoot. The first several teams to do that were taking easy kills. The problem is that I couldn't see the ships' action with my own eyes, so I and some team members working on `ropship` went on-site and started to devise responsive strategies. At this point I realized that what we needed now isn't a complete, failproof strategy, but a static strategy that we're able to change easily at each round. As we weren't even able to control our ship, I devised a stack pivoting ROP chain with `tick value * const(0x40?)` and our ship started to do something.

From that point, our ROP chain remained static with strategies changing over rounds. A rough overview of how our strategy changed over time is like this:
1. Stick to the wall, rotate to face enemies, then weave & shoot & shield whenever possible.
2. Stick to the wall, scan the map perimeter & shoot & shield whenever possible. This is highly likely to beat strategy 1, since most do not weave over something like 120 degrees.
3. Run in circles smaller than the map perimeter, shoot & shield whenever possible. This is highly likely to beat strategy 2 since ships with strategy 2 would not be able to attack ships with strategy 3, but it may be possible in the other way.

Our team was able to squeeze out most of the score with strategy 2. After implementing strategy 3, one of our team member tried to implement reactive armor by checking distance with all the bullets and turning on the shield if any gets too close. The challenge sadly closed before it was done.

While I was deeply involved in `ropship`, a new A&D challenge `aoool` was released. However, I did not have any time to take a look at that challenge. Just before the end of the first day of the competition, a new A&D challenge `AI Han Solo` was released. I started to work on that challenge.

---

### Day 1 Night ~ Day 2 Morning

As I have almost no knowledge in AI or ANNs, I could not immediately find out how to approach the `AI Han Solo` challenge. With assistance of my teammates, I recognized that the problem is to recover data from an ANN classifier. Specifically, a network is trained to classify an image with 16 hex digits into 256 classes, the first 16 (0th~15th) being `0000000000000000`, `1111111111111111`, ... up to `FFFFFFFFFFFFFFFF`, the 16th being some value we must recover, 17th being some hash of the value of 16th value, and so on such that `N+1`th classifies some hash of `N`th value.

Our team had no one involved in ML, so we had a hard time doing virtually anything. We tried everything we had in mind, but to no avail. Brute force? Generative Adversarial Networks? I was completely lost of what to do. As I got too tired and irritated with ML stuff, I decided to take a short nap.

After I recovered my mental tranquility, I got my hands on the challenge again. As the challenge is quite similar to the DEF CON CTF 26 Quals `flagsifier` challenge, my teammates decided to find some input that maximizes the activation of 16th neuron (16th class). I quickly coded an optimizer with simulated annealing, and with some parameter optimization was able to recover about 75% of the hex digits correctly. I tried classifying a class whose value I already know, for example 0th class. It seemed that if I supply my optimizer with a value which already has 50% of the hex digits correct, it is likely to recover most of the digits. Also, even if the optimizer runs with random values, it managed to recover quite a lot of digits.

My teammates and I all focused on how to attack other teams' network, but disregarded the defense side. This is because we weren't even sure if optimization would work or not, and so did not know exactly what the problem is and how to fix the network. As we scrambled to somehow make my optimizer working, the second day of the competition started.

---

## Day 2

I've expected my optimizer to not recover all the hex digits, so I tried with some brute force search based on results above some threshold. However, that still not yield the answer, not to even mention that it was running at ~~uselessly~~ slow speed. After some rounds passed, we were finally able to recover our own network's key and get our own flag. Now it's time to try attacking other teams' network, but the optimizer was too slow to effectively attack other teams. Well, it might not have been that slow, but might just be that there is a certain threshold in the number of possible digits that we can optimize with simulated annealing changing at most one character at a time.

But... we haven't even thought of how to reinforce our network! We were getting attacked hopelessly. I left the attacking process to my teammates, and started to train our network. Since simply changing our network would require other teams to put in their computing power, I tried to train the same network as given with only the secret values changed. However, this in itself required a lot of computing power, and I managed to get a trained network accepted after several minutes of training. This defense probably wasn't effective, since we just trained the same vulnerable network. Until the problem went down, we weren't able to defend nor attack.

Three new challenges were released, which were `dooom` (KotH), `mirror-universe` (A&D), and `babi` (A&D). I went down on-site to try out `dooom`. The challenge ran on an original xbox with customized `Doom` game. The game binary gets sent over the server at boot, so we first needed to get that binary by capturing packets - and we had no device that could capture packets easily. We used some *dark networking magic* by bridging several devices, and then were able to capture packets. The game was made so that:
1. We should prefix our player's name with our team index `[05]` to score. The default player name is `sheep`.
2. Shooting is blocked on client side.

It was quite easy patching those two, and then the only thing left trying it out is applying that binary to our xbox and running it. We tried a man-in-the-middle attack on our own xbox to swap the binary with our patched one. Guess what? We weren't able to do this until the challenge closed.

Honestly, this day was a disaster for me - until the `bitflip-conjecture` (KotH) was out at the end of the day. The challenge is to write a x64 machine code not more than 200 bytes that prints out `"I am invincible!"` and exits with exit code 0. The problem here is that it must do the same thing when any one of the 1600 bits is flipped. There are three modes of running the code, as the binary tells us:
1. I like all my registers set to zero
2. I want them pointing to the middle of a 64KB R/W region of memory)
3. Dont bother. Leave them as they are
After the lesson learned painfully on `ropship`, we split into two different roles: some worked on making the shortest code, and some other teammates and I tried to find out a clever way to somehow evade the flipped part. We first started submitting the short code with mode 1 and managed to get some points.

One of my teammates thought of planting three identical code and using `repe` prefix to find the flipped location, then recover or simply run non-flipped code section. This gave me a sparking idea - if we use mode 3, wouldn't there be information about the flipped byte/bit? And yes sure there is, in `rdx` register! I quickly came up with a 5 byte jump code that jumps to unflipped code between two initially identical code. Initially, this code was resistant except 25 bits. From there on, we fiddled with nop-sledding and easily reached 10 bits. Until almost the last round at the end of the day we stayed in the first place, sqeezing out quite a large amount of points.

At the end of the second day of competition, a new challenge `super-smash-ooos` (A&D) was released, which I have not looked into.

---

### Day 2 Night ~ Day 3 Morning

There isn't much to talk about at this time; I took a short nap, got my hands back on `bitflip-conjecture`, and our team made the code resistant to all bitflips except one single bit. We weren't completely satisfied with one bit left, but decided to work on other challenges. I tried bruteforcing several instructions such that it becomes completely resilient, but my computing power seemed to be insufficient.

---

## Day 3

As expected, there were no teams that completed the `bitflip-conjecture`, and many teams were stuck on the last single bit. After some time, however, Tea Deliverers managed to make it completely bitflip-resistant. Since I thought that filling up the last bit would be infeasible before challenge closes, I looked into `super-smash-ooos` for a short time before `jtaste` (A&D) came out.

`jtaste` was a very simple web challenge. We were given a .js file, and after a short time analyzing the code we found out a problem with blacklisting characters & `unidecode` being able to create those characters later on. We quickly fixed the code by simply removing unidecode and spun up an attack script, but was only able to attack twice (and these were the only attacks we succeeded throughout three days).

The competition ended shortly, with our team ranking 12 out of 16 teams. 

---

## About the challenges

Overall, the challenges were fun, especially KotH problems. Below is how I **personally** think about each challenges that I've worked on, and does not represent our team's opinion nor is trying to offend anyone.
 - `ropship`: Very fun, visualizer was a great idea; Watching hundreds of lines of text data would have been much boring. However, the time limit was too strict for any map-aware strategy, so maybe releasing it few hours before end of day 1 & continuing several hours after day 2 start would have been much more fun.
  - `AI Han Solo`: An interesting problem, but depends so much on computing power on both attack & defense. I had no strong computing power at hand, so I needed to run everything on a VM running Ubuntu on a laptop :(
  - `dooom`: We were notified that we need a display with hdmi, but not a packet-sniffable/MitM-friendly router. We spent all the time setting up stuff, maybe giving xbox + router would have been better. Also, the scores seemed to be dependent on Doom playing skills, I dunno if this is intentional or not.
  - `bitflip-conjecture`: Again, very fun. Gave me many ideas to think about. Would a 2-bit resistant code have been possible? If not, would it be possible to prove it? Is there a bitflip-resistant ISA? A register bitflip-resistant code?
  - `jtaste`: Vulnerability and fix both were too obvious. Bluntly speaking, seemed like an incomplete challenge, or a challenge to fill up the remaining time of last day. Reminded me of the speedrun chals.

---

## In retrospect...

1. On `ropship`, trying to come up with a hard strategy from the start was a miscalcuated move; KotH is not about devising a one-stop solution, but is about building up a solution from something that barely works ASAP.
2. Maybe working on KotH problems so much wasn't a tactical move? Attack and Defense scores take up 40% of the total score respectively, and KotH only takes up 20% of maximum score. Tackling an A&D problem is 4 times more worthy than tackling a KotH problem with just the max scores compared. But our team scored about 40% of our total score from KotH and the remaining 60% from defense, so maybe working on KotH still paid off...
3. I and our team need to be better prepared for such on-site CTF competition. There are several factors to improve:
    1. From the start and throughout the competition, our server & VPN connection was constantly dropping, and the server had IP constantly changing. It was grudging to access services.
    2. Our hardware isn't sufficiently prepared. We had no packet sniffing & MitM friendly router to use, which costed us a whole challenge `dooom`. We had no machine with sufficient computing power to try bruteforce in `AI Han Solo` or `bitflip-conjecture`. Maybe spinning up a compute cloud instance if necessary might suffice.