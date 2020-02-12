#pragma once

// We can use std::complex instead
// Using custom class for clarity
class Coord
{
private:
	int _w, _h;
public:
	const int &w = _w, &h = _h;

	Coord() {}
	Coord(int w, int h) : _w(w), _h(h) {}

	Coord operator+(const Coord& rhs) const {
		return Coord(w + rhs.w, h + rhs.h);
	}
	Coord operator-() const {
		return Coord(-w, -h);
	}
	Coord operator-(const Coord& rhs) const {
		return *this + (-rhs);
	}
	Coord operator*(const int rhs) const {
		return Coord(w*rhs, h*rhs);
	}
	Coord operator=(const Coord &rhs) {
		_w = rhs.w;
		_h = rhs.h;
		return *this;
	}

	bool operator<(const Coord& rhs) const {
		return w < rhs.w && h < rhs.h;
	}
	bool operator>(const Coord& rhs) const {
		return w > rhs.w && h > rhs.h;
	}
	bool operator==(const Coord& rhs) const {
		return w == rhs.w && h == rhs.h;
	}
	bool operator<=(const Coord& rhs) const {
		return w <= rhs.w && h <= rhs.h;
	}
	bool operator>=(const Coord& rhs) const {
		return w >= rhs.w && h >= rhs.h;
	}

	bool inRange(const Coord& minCrd, const Coord& maxCrd) const {
		return *this >= minCrd && *this < maxCrd;
	}
};

typedef enum {
	ST_STOPPED = 1,
	ST_RUNNING = 2,
	ST_QUIT    = 4,
	ST_STRMODE = 8,
} State;