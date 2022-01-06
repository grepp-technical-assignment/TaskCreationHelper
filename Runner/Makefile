PROC_NAME = tch

CC = gcc
CFLAGS = -Wall -Werror -std=c99 -pedantic -O2 -fPIC

ifeq ($(OS),Windows_NT)
    RM = del /Q /F
    RRM = rmdir /Q /S
	PROC_DEFAULT_PATH ?= bin
	MKDIR = mkdir
	SRC_PATH = src
	OBJ_PATH = obj
	INCLUDE_PATH = include
else
    RM = rm -f
    RRM = rm -f -r
	CAT = cat
	MKDIR = mkdir -p
	PROC_DEFAULT_PATH ?= /usr/local/bin
	SRC_PATH = ./src
	OBJ_PATH = ./obj
	INCLUDE_PATH = ./include
endif

TCH_VERSION = $(shell cat $(PWD)/../VERSION)
SRCS = $(notdir $(wildcard $(SRC_PATH)/*.c))
OBJS = $(SRCS:.c=.o)
OBJECTS = $(patsubst %.o,$(OBJ_PATH)/%.o,$(OBJS))

install: $(PROC_NAME)
.PHONY: install

$(OBJ_PATH)/%.o: $(SRC_PATH)/%.c | $(OBJ_PATH)
	@echo "compilation $<"
	@$(CC) -o $@ $(CFLAGS) -I $(INCLUDE_PATH) -DTCH_VERSION=\"$(TCH_VERSION)\" -c $<

$(OBJ_PATH):
	@$(MKDIR) $(OBJ_PATH)
.PHONY: $(OBJ_PATH)/%.o

$(PROC_NAME): $(OBJECTS) | $(PROC_DEFAULT_PATH)
	@echo "installation tch-runner"
	@$(CC) -o $(PROC_DEFAULT_PATH)/$(PROC_NAME) $(CFLAGS) $(OBJECTS)
	@$(RRM) $(OBJ_PATH)

$(PROC_DEFAULT_PATH):
	@$(MKDIR) $(PROC_DEFAULT_PATH)
.PHONY: $(PROC_NAME)

uninstall:
	@echo "uninstallation tch-runner"
	@$(RM) $(PROC_DEFAULT_PATH)/tch
.PHONY: uninstall

clean:
	@echo "clean tch-runner"
	@$(RRM) $(OBJ_PATH)
.PHONY: clean