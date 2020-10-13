# Task Creation Helper

This repository is made by Azad to make task creation process easier in [Business Programmers platform](https://business.programmers.co.kr/). 
I strongly recommend you to use Visual Studio Code for convenience, but you can use other IDEs as well.

# Features

1. Input data generation: You can generate the input data easily. You just have to write one function - `generate`.
2. Input data validation: You can validate data easily. Type assertion is internally done, so you can focus customized validation only. You just have to write one function - `validate`.
3. Execution and comparison between multiple solution files: You can label an expected verdict for each solution file, and TCH will automatically verify it.
4. Output data generation: You don't have to generate output data explicitly. Instead, TCH will generate output data by main AC solution file.

All things above are possible in only one command. All dirty background jobs will be handled by TCH. You can focus on tasks itself.

# Dependencies

* Python 3.8.3+
  * autopep8 (for contributing)
* C++17 or above (If you want to use C++)
  * g++ 7.5.0 or above
* Warning: WSL 1 is **not safe** to use this library due to [lack of resource management](https://github.com/microsoft/WSL/issues/4509).

# Usage

## Run: `run.py`

You can use TCH by running `run.py`. Enter `python3 run.py --help` on terminal to learn usage. Also, please check out `Examples` folder to look showcases.

## Configuration: `config.json`

For each task, you should set the configuration json file to maintain whole task data. In `config.json`, you can maintain following things:

- `name`: Name of task.
- `author`: Author of task.
- `parameters`: Information of parameters of solution function. Each parameters have following information;
  - `name`: Name of parameter. This name should qualify all of some major languages' variable name standard.
  - `type`: Type of parameter. `int`, `long`, `str`, `bool`, `float`, `double` are available.
  - `dimension`: Dimension of parameter. 0 means raw value, 1 means linear array, and 2 means rectangular array. 3 or more isn't supported since Business Programmers Platform does not support it too.
- `return`: Information of return value of solution function. This should have following information;
  - `type`: Same as `parameters.type`.
  - `dimension`: Same as `parameters.dimension`.
- `limits`: Information of limits under solution execution.
  - `time`: Time limit of solution execution. If some solution file's execution time exceeds this on some data, then it will get `TLE` verdict on that data.
  - `memory`: Memory limit of solution execution. If some solution program encounters memory limit during execution on some data, then it will get `MLE` verdict on that data.
- `solutions`: List of solution files. You can label expected verdict for each solution file. You can even label multiple expected verdicts for single solution file. Check the examples to know how to do it.
- `generators`: List of generator files. You should give a short name for each generators. That names will be used in `genscript`.
- `genscript`: `genscript` is shorter name of "Generator Script". Put list of genscripts, then each genscript will call generators and pass arguments. For example, `generator_name arg1 arg2 ...` will call `generate([arg1, arg2, ...])` in `generator_name`'s generator file. Genscript also supports comment, which makes you can temporary disable some of genscripts.
- `log`: Log file's path. You can watch detailed logs(logged by library) in this file.
- `iofiles`: Information of I/O data files to upload at Business Programmers platform.
  - `path`: Base path of I/O files. All I/O files will be made under this folder.
  - `inputsyntax`: Syntax of name of input files. Should contain "%d" or similar.
  - `outputsyntax`: Syntax of name of output files. Should contain "%d" or similar.
- `validator`: Validator file. It's ok to leave this as blank(then TCH will execute solutions without validating generated input data), but I strongly recommend to make one.
- `precision`: In case your solution is returning floating point numbers, you can set the precision to determine return values as AC or WA.
- `version`: Version information.
  - `problem`: Version of this task. You can set arbitrary value for this.
  - `config`: Version of `config.json` format.

Initialize problem folder with Azad library, then you will get sample configuration json file in that problem folder.

# Planned Future Features

These are currently unsupported, but targetted to be supported in future.

- Cross language sourcefile execution for current unsupported languages
- `config.json` versioning
- Customized answer checker
- Safe virtualization using Docker or something similar

# Concept Details

## Source Files

Source files are the files you have to write to make a task. Source files will generate each input data and output data with several validations. There are multiple categories of source files you can register on `config.json`;

1. **Generator**: Generates input data for solution function. Followings are function shapes you should define in each language.
   - Python3: `def generate(args: list) -> dict`
   - C++17: `void generate(std::vector<std::string> genscript, param1_type &param1, param2_type &param2, ...);`
   
2. **Validator**: Validates the input data generated by Generator. You don't have to make any return in validate function. If there is any hazard on data, then print the message to stderr and raise an error. Followings are function shapes you should define in each language.
   - Python3: `def validate(param1: param1_type, param2: param2_type, ...) -> None`
   - C++17: `void validate(param1_type param1, param2_type param2, ...);`
   
3. **Solution**: Produces the output data with input data generated by Generator. In other words, this is the solution source code which you should be able to submit it to Programmers Platform directly. You can assign multiple solution verdicts in each solution file; Please check *Solution Verdicts* below.
   - Python3: `def solution(param1: param1_type, param2: param2_type, ...) -> return_type`
   - C++17: `return_type solution(param1_type param1, param2_type param2, ...);`

### Notes

- Python3 has priority for support since this library is developed under Python3.
- All files will be executed under `stdout = os.devnull`, so any standard output in original source files will be ignored. I recommend you to raise an error or exit with invalid code instead.

## Solution Verdicts

There are 5 solution verdicts. You have to assign at least one of those verdicts to each solution.

1. **AC**: Short name of "Accepted". Give this when the solution is expected to generate correct answer on all(or partial, if multi-categorized) cases.
2. **WA**: Short name of "Wrong Answer". Give this when the solution is expected to generate wrong answer on some cases.
3. **TLE**: Short name of "Time Limit Exceeded". Give this when the solution is expected to execute too long on some cases.
4. **MLE**: Short name of "Memory Limit Exceeded". This verdict is not reliable yet, so I recommend you to use *FAIL* instead for now. I am planning to support this in near future.
5. **FAIL**: Short name of "Failure". Give this when the solution is expected to raise an runtime error on some cases.

## I/O Data Protocol

There are two types of I/O Data Protocol in TCH.

1. **Internal Primitive**: This protocol is for internal data transfer. All data is represented as integer. This protocol is used to communicate between main program, generators, validators and solutions.
2. **Programmers Business**: This protocol is for Programmers Business platform. It is similar to json. When the program is successfully executed(in either *Full* or *Produce* mode), the resulting file will be optimized for Programmers Business platform. You can upload these files on that platform directly.

## Process Exit Codes

*WIP*

# Changelog

## v0.0: Init

- The first working version of TCH! Most of very basic concepts are made here.
- This version was developed under some other private repository.

## v0.1: Concurrency 1

- Applied concurrency on sourcefile execution using `multiprocessing` module.
- Added temporary file system feature.

## v0.2: Native Logging

- Replaced custom logging library by standard logging library.

## v0.3: Concurrency 2

- Changed background mechanism of concurrency.
  - Now total number of processes are limited by available CPU count.
- Now TCH provides very basic statistics of process execution times.

## v0.4: Cross Language Execution

- Now supports cross language execution. Also changed fundamental background of concurrency again.
- Supported languages: Python3, C++17

## v0.5: Unspecified Title

- Now `run.py` is opt-parsing; You can pass options via dash highlighting.