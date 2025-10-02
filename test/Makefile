CC = gcc
CFLAGS = -Wall -Wextra -std=c11

test_driver: test_driver.c _test.h
	$(CC) $(CFLAGS) -o test_driver test_driver.c

clean:
	rm -f test_driver

.PHONY: clean
