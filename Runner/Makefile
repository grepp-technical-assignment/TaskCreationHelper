PROC_NAME = tch

ifeq ($(OS),Windows_NT)
    RM = cmd //C del //Q //F
    RRM = cmd //C rmdir //Q //S
	CAT = type
	PROC_DEFAULT_PATH ?= ./
else
    RM = rm -f
    RRM = rm -f -r
	CAT = cat
	PROC_DEFAULT_PATH ?= /usr/local/bin
endif

CC = gcc
CFLAGS = -Wall -Werror -std=c99 -pedantic -O2 -fPIC
SRC_PATH = ./src
OBJ_PATH = ./obj
INCLUDE_PATH = ./include
TCH_VERSION = $(shell $(CAT) $(PWD)/../VERSION)
SRCS = $(notdir $(wildcard $(SRC_PATH)/*.c))
OBJS = $(SRCS:.c=.o)

OBJECTS = $(patsubst %.o,$(OBJ_PATH)/%.o,$(OBJS))

install: $(PROC_NAME)
.PHONY: install

$(OBJ_PATH)/%.o: $(SRC_PATH)/%.c
	@echo "compilation $<"
	@mkdir -p $(OBJ_PATH)
	@$(CC) -o $@ $(CFLAGS) -I $(INCLUDE_PATH) -DTCH_VERSION=\"$(TCH_VERSION)\" -c $<
.PHONY: $(OBJ_PATH)/%.o

$(PROC_NAME): $(OBJECTS)
	@echo "installation tch-runner"
	@$(CC) -o $(PROC_DEFAULT_PATH)/$(PROC_NAME) $(CFLAGS) $(OBJECTS)
	@rm -rf $(OBJ_PATH)
.PHONY: $(PROC_NAME)

uninstall:
	@echo "uninstallation tch-runner"
	@rm -f $(PROC_DEFAULT_PATH)/tch
.PHONY: uninstall

clean:
	@echo "clean tch-runner"
	@rm -rf $(OBJ_PATH)
.PHONY: clean