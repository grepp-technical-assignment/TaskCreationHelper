# Task Creation Helper

This repository is made by Azad to make task creation process easier in [YBM Business Programmers platform](https://ybm-business.programmers.co.kr/). 
I strongly recommend you to use Visual Studio Code for convenience, but you can use other IDEs as well.

# Features

- Maintanence of parameter/return type and dimension
- Data generation with generator and genscript
- Source file validation (Python3)
- Automated I/O file generation (YBM style formatted)

# Dependencies

* Python 3.8.3+
* direnv
* pyenv

# Usage

## Azad library

This python library includes core functionalities. 
Look `AzadLibrary` folder to read sourcecode.
If you want to avoid using CLI, I recommend you to use following tasks in Visual Studio Code.

You can use Azad library by running `run.py`. 
Enter `python3 run.py help` on terminal to learn usage.

## Configuration: `config.json`

For each problem, you should set the configuration json file to maintain whole problem data. 
In `config.json`, you can maintain following things:

- Parameters and return value's variable type
  - Each parameter will have 3 options - variable name, type and dimension.
- Time and memory limit (Memory limit is currently unsupported)
- Solution files: List of solution files are here. Those are classified by following categories.
  - AC: Official solution. This should pass all test cases. Especially, the first AC solution will generate all answer data.
  - WA: Wrong Answer. This should return wrong answer at least one of test cases.
  - FAIL: This should fail(with any reason, including timeout and system fails) at least one of test cases.
  - TLE: This should exceed time limit at least one of test cases.
- Generator files: List of generator files are here. Each generator should have own name, which will be used in `genscript`.
- Generator script(`genscript`): This is the script to use generate input data with generators. Comments are also supported.
- I/O file storage directory
- Input validator

Initialize problem folder with Azad library, then you will get sample configuration json file in that problem folder.

# Planned Future Features

These are currently unsupported, but targetted to be supported in future.

- Customized answer checker
- Applying Time/Memory limit on solution file execution
- Cross language sourcefile execution(C++, Java, etc)

