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
* C++17 or above
  * gcc (C++17 support version)
  * [Nlohmann's Modern C++ Json Library](https://github.com/nlohmann/json) (Will be automatically installed)
* Warning: WSL 1 is **not safe** to use this library due to [lack of resource management](https://github.com/microsoft/WSL/issues/4509).

# Usage

## Run: `run.py`

You can use TCH by running `run.py`. Enter `python3 run.py help` on terminal to learn usage.

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

- (WIP) Cross language sourcefile execution(C++17, Python3, etc)
- `config.json` versioning
- Customized answer checker
