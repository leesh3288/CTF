#define _CRT_SECURE_NO_WARNINGS

#include <chrono>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <limits>
#include <random>
#include <string>
#include <vector>
#include "CTFHelper.h"
#include "types.h"

#define MAXW 80
#define MAXH 25
#define TIMEOUT 120
#define STACK_LIMIT 0x100
#define STEP_LIMIT 0x10000


struct {
	Coord size;
	std::string inst[MAXH];
} code;

const Coord ORIGIN(0, 0), RIGHT(1, 0), LEFT(-1, 0), UP(0, -1), DOWN(0, 1);


std::mt19937_64 &GetRng();
void RecvCode();
void RunDebugger();
void RunStep(Coord &pos, const Coord *&dir, std::vector<unsigned char> &stack, State &state, bool cycle, int &total_steps);
static inline void CheckCrd(const Coord &crd, const char *msg);

template<typename T>
T ExPop(std::vector<T> &vec);
template<typename T>
void ExPush(std::vector<T> &vec, T val);
void StepIncr(int &steps);


int main(void)
{
	CTF_IOInit();
	CTF_SetTimer(TIMEOUT);

	RecvCode();
	RunDebugger();

	return 0;
}

std::mt19937_64 &GetRng()
{
	static bool isInited = false;
	static std::mt19937_64 mt;

	if (!isInited)
	{
		std::random_device rd;
		mt.seed(rd());
		isInited = true;
	}

	return mt;
}

void RecvCode()
{
	int width, height;

	std::cin >> width >> height;
	if (!std::cin.good() || width <= 0 || height <= 0 || width > MAXW || height > MAXH)
	{
		exit(EXIT_FAILURE);
	}
	code.size = Coord(width, height);

	std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
	for (int i = 0; i < (signed)code.size.h; i++)
	{
		std::string &curline = code.inst[i];
		std::getline(std::cin, curline);
		if (!std::cin.good())
			exit(EXIT_FAILURE);

		// "jagged" 2d code
		if (curline.length() > code.size.w)
			curline.resize(code.size.w);  // shrink to fit
	}
}

void RunDebugger()
{
	Coord pos(0, 0);
	const Coord *dir = &RIGHT;
	std::vector<unsigned char> stack;
	State state = ST_STOPPED;
	std::string action;
	bool cycle;
	int total_steps = 0;

	do
	{
		cycle = false;
		std::cout << "> ";
		std::cin >> action;
		if (std::cin.good())
		{
			if (!action.compare("quit"))
				state = ST_QUIT;
			else if (!action.compare("run"))
			{
				if (state & ST_RUNNING)
					std::cout << "Program already running." << std::endl;
				else
				{
					state = ST_RUNNING;
					pos = ORIGIN;
					dir = &RIGHT;
					stack.clear();
					std::cout << "Program started." << std::endl;
				}
			}
			else if (!action.compare("stop"))
			{
				if (state & ST_RUNNING)
				{
					state = ST_STOPPED;
					std::cout << "Program stopped." << std::endl;
				}
				else
					std::cout << "Program not running." << std::endl;
			}
			else if (!action.compare("step") || (cycle = !action.compare("cycle")))
			{
				int cnt;

				std::cin >> cnt;
				if (std::cin.good())
				{
					if (state & ST_STOPPED)
						std::cout << "Program not running." << std::endl;
					else
					{
						int si;
						bool crashed = false;

						try
						{
							for (si = 0; si < cnt && (state & ST_RUNNING); si++)
								RunStep(pos, dir, stack, state, cycle, total_steps);
						}
						catch (const std::range_error &e)  // global step limit
						{
							state = ST_STOPPED;
							crashed = true;
							std::cout << "Debugger terminated: " << e.what() << std::endl;
							break;
						}
						catch (const std::exception &e)
						{
							state = ST_STOPPED;
							crashed = true;
							std::cout << si << " " << (cycle ? "cycle" : "step") << "(s) executed." << std::endl;
							std::cout << "Program terminated: " << e.what() << std::endl;
						}
						if (!crashed)
						{
							std::cout << si << " " << (cycle ? "cycle" : "step") << "(s) executed." << std::endl;
							if (state & ST_STOPPED)
								std::cout << "Program stopped." << std::endl;
						}
					}
				}
				else
					break;
			}
			else if (!action.compare("stack"))
			{
				std::cout << "Stack Dump:" << std::endl;
				for (auto it = stack.crbegin(); it != stack.crend(); it++)
					std::cout << std::hex << std::setw(2) << std::setfill('0') << static_cast<unsigned>(*it) << std::endl;
				std::cout << std::dec;
			}
			else if (!action.compare("pc"))
				std::cout << "PC: (" << pos.w << ", " << pos.h << ")" << std::endl;
			else
				std::cout << "Unknown command '" << action << "'." << std::endl;
		}
		else
			break;
	} while (!(state & ST_QUIT));
}

void RunStep(Coord &pos, const Coord *&dir, std::vector<unsigned char> &stack, State &state, bool cycle, int &total_steps)
{
	// step mode: only process one character
	// cycle mode: complete a whole non-jump command
	
	// current pos in valid state
	unsigned char op = code.inst[pos.h][pos.w];

	if ((state & ST_STRMODE) && op != '"')
	{
		if (!cycle)
		{
			StepIncr(total_steps);
			ExPush(stack, op);
		}
		else
		{
			// push until end of string
			do
			{
				StepIncr(total_steps);
				ExPush(stack, op);
				pos = pos + *dir;
				CheckCrd(pos, "PC out of range");
				op = code.inst[pos.h][pos.w];
			} while (op != '"');
			state = static_cast<State>(state ^ ST_STRMODE);
		}
	}
	else
	{
LBL_CONT:  // godforsaken GOTO >> while(true) + continue/breaks
		
		if (cycle)
		{
			while (op == ' ')
			{
				StepIncr(total_steps);
				pos = pos + *dir;
				CheckCrd(pos, "PC out of range");
				op = code.inst[pos.h][pos.w];
			}
		}

		StepIncr(total_steps);

		switch (op)
		{
			case '0': case '1': case '2': case '3': case '4':
			case '5': case '6': case '7': case '8': case '9': {
				ExPush(stack, static_cast<unsigned char>(op - '0'));
			} break;
			case 'a': case 'b': case 'c': case 'd': case 'e': case 'f': {
				ExPush(stack, static_cast<unsigned char>(op - 'a' + 10));
			} break;
			case '+': {
				unsigned char rhs, lhs;
				rhs = ExPop(stack);
				lhs = ExPop(stack);
				ExPush(stack, static_cast<unsigned char>(rhs + lhs));
			} break;
			case '-': {
				unsigned char rhs, lhs;
				rhs = ExPop(stack);
				lhs = ExPop(stack);
				ExPush(stack, static_cast<unsigned char>(rhs - lhs));
			} break;
			case '*': {
				unsigned char rhs, lhs;
				rhs = ExPop(stack);
				lhs = ExPop(stack);
				ExPush(stack, static_cast<unsigned char>(rhs * lhs));
			} break;
			case '/': {
				unsigned char rhs, lhs;
				rhs = ExPop(stack);
				lhs = ExPop(stack);
				if (lhs == 0)
					throw std::runtime_error("Divide by zero");
				ExPush(stack, static_cast<unsigned char>(rhs / lhs));
			} break;
			case '%': {
				unsigned char rhs, lhs;
				rhs = ExPop(stack);
				lhs = ExPop(stack);
				if (lhs == 0)
					throw std::runtime_error("Remainder by zero");
				ExPush(stack, static_cast<unsigned char>(rhs % lhs));
			} break;
			case '!': {
				unsigned char val = ExPop(stack);
				ExPush(stack, static_cast<unsigned char>(!val));
			} break;
			case '`': {
				unsigned char rhs, lhs;
				rhs = ExPop(stack);
				lhs = ExPop(stack);
				ExPush(stack, static_cast<unsigned char>(rhs < lhs));
			} break;
			case '>': {
				dir = &RIGHT;
			} break;
			case '<': {
				dir = &LEFT;
			} break;
			case '^': {
				dir = &UP;
			} break;
			case 'v': {
				dir = &DOWN;
			} break;
			case '?': {
				static const Coord *dirs[] = { &RIGHT, &LEFT, &UP, &DOWN };
				static const std::uniform_int_distribution<int> dist(0, 3);
				dir = dirs[dist(GetRng())];
			} break;
			case '_': {
				unsigned char pred = ExPop(stack);
				if (pred == 0)
					dir = &RIGHT;
				else
					dir = &LEFT;
			} break;
			case '|': {
				unsigned char pred = ExPop(stack);
				if (pred == 0)
					dir = &DOWN;
				else
					dir = &UP;
			} break;
			case '"': {
				state = static_cast<State>(state ^ ST_STRMODE);
			} break;
			case ':': {
				unsigned char v = ExPop(stack);
				ExPush(stack, v);
				ExPush(stack, v);
			} break;
			case '\\': {
				unsigned char fst, snd;
				fst = ExPop(stack);
				snd = ExPop(stack);
				ExPush(stack, fst);
				ExPush(stack, snd);
			} break;
			case '$': {
				ExPop(stack);
			} break;
			case '.': {
				std::cout << static_cast<unsigned>(ExPop(stack)) << " ";
			} break;
			case ',': {
				std::cout << ExPop(stack);
			} break;
			case '#': {
				/// BUG: No CheckCrd(pos) validation, chaining this with other bugs lead to arbitrary relative RW
				if (cycle)
				{
					pos = pos + *dir * 2;
					op = code.inst[pos.h][pos.w];
					goto LBL_CONT;
				}
				else
					pos = pos + *dir;
			} break;
			case 'p': {
				unsigned char y, x, v;
				y = ExPop(stack);
				x = ExPop(stack);
				v = ExPop(stack);
				CheckCrd(Coord(x, y), "Put operation out of range");
				code.inst[y][x] = v;
			} break;
			case 'g': {
				unsigned char y, x;
				y = ExPop(stack);
				x = ExPop(stack);
				CheckCrd(Coord(x, y), "Get operation out of range");
				ExPush(stack, static_cast<unsigned char>(code.inst[y][x]));
			} break;
			case '&': {
				int v;
				if (!(std::cin >> v))
					throw std::runtime_error("Invalid input");
				ExPush(stack, static_cast<unsigned char>(v & 0xff));
			} break;
			case '\'': {
				/// BUG: No CheckCrd(pos) validation, leading to single byte overread
				pos = pos + *dir;
				ExPush(stack, static_cast<unsigned char>(code.inst[pos.h][pos.w]));
			} break;
			case 's': {
				/// BUG: No CheckCrd(pos) validation, leading to single byte overwrite
				pos = pos + *dir;
				code.inst[pos.h][pos.w] = ExPop(stack);
			} break;
			case 'x': {
				code.inst[pos.h][pos.w] = ExPop(stack);
			} break;
			case '@': {
				state = ST_STOPPED;
			} break;
			case ' ':
				break;  // non-cycle
			default:
				throw std::runtime_error("Illegal instruction");
		}
	}

	if (state & ST_RUNNING)
	{
		pos = pos + *dir;
		CheckCrd(pos, "PC out of range");
	}
}

static inline void CheckCrd(const Coord &crd, const char *msg)
{
	if (!crd.inRange(ORIGIN, code.size) || crd.w < 0 || crd.w >= code.inst[crd.h].length())
		throw std::out_of_range(msg);
}

template<typename T>
T ExPop(std::vector<T> &vec)
{
	T val;
	if (vec.size() == 0)
		throw std::out_of_range("Pop against empty stack");
	val = vec.back();
	vec.pop_back();
	return val;
}

template<typename T>
void ExPush(std::vector<T> &vec, T val)
{
	if (vec.size() == STACK_LIMIT)
		throw std::out_of_range("Push against full stack");
	vec.push_back(val);
}

void StepIncr(int &steps)
{
	if (steps++ >= STEP_LIMIT)
		throw std::range_error("Global step limit reached");
}