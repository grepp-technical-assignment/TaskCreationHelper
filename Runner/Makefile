PROC_DEFAULT_PATH ?= /usr/local/bin
PROC_NAME = tch

CC = gcc
CFLAGS = -Wall -Werror -std=c99 -pedantic -O2 -fPIC
SRC_PATH = ./src
OBJ_PATH = ./obj
INCLUDE_PATH = ./include
SRCS = $(notdir $(wildcard $(SRC_PATH)/*.c))
OBJS = $(SRCS:.c=.o)

OBJECTS = $(patsubst %.o,$(OBJ_PATH)/%.o,$(OBJS))

.PHONY: install uninstall clean

install: $(PROC_NAME)

$(OBJ_PATH)/%.o: $(SRC_PATH)/%.c
	@echo "compilation $<"
	@mkdir -p $(OBJ_PATH)
	@$(CC) -o $@ $(CFLAGS) -I $(INCLUDE_PATH) -c $<

$(PROC_NAME): $(OBJECTS)
	@echo "installation tch-runner"
	@$(CC) -o $(PROC_DEFAULT_PATH)/$(PROC_NAME) $(CFLAGS) $(OBJECTS)
	@rm -rf $(OBJ_PATH)

uninstall:
	@echo "uninstallation tch-runner"
	@rm -f $(PROC_DEFAULT_PATH)/tch

clean:
	@echo "clean tch-runner"
	@rm -rf $(OBJ_PATH)