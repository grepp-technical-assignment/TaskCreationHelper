function typeCheck(obj, type, dim) {
    if (dim < 0) throw new Error('typeCheck error: dim is negative');
    if (dim > 0) {
        if (Array.isArray(obj)) {
            for (var i = 0; i < obj.length; i++) {
                typeCheck(obj[i], type, dim - 1);
                if (dim > 1) {
                    if (obj[i].length != obj[0].length) throw new Error('typeCheck error: matrix is not square');
                }
            }
        } else {
            throw new Error('typeCheck error: input dimension mismatch');
        }
    } else {
        switch (type) {
        case 'int': case 'long':
            if (!Number.isInteger(obj)) throw new Error('typeCheck error: input is not integer');
            break;
        case 'float':
            if (!Number.isFinite(obj)) throw new Error('typeCheck error: input is not float');
            break;
        case 'string':
            if (!typeof obj === 'string') throw new Error('typeCheck error: input is not string');
            break;
        case 'bool':
            if (!typeof obj === 'boolean') throw new Error('typeCheck error: input is not boolean');
            break;
        default:
            throw new Error('typeCheck error: unknown type');
        }
    }
}

function parse0d(obj, type) {
    switch (type) {
    case 'int': case 'long':
        return parseInt(obj);
    case 'float':
        return parseFloat(obj);
    case 'string':
        return obj;
    case 'bool':
        return obj === 'true';
    default:
        return null;
    }
}

function parse(input, type, dim, checkAssert = true) {
    if (dim < 0) throw new Error('parse error: dim is negative');
    if (dim > 0) {
        var length = parse0d(input.shift(), 'int');
        var obj = [];
        if (input.length < length) throw new Error('parse error: input is empty');
        for (var i = 0; i < length; ++i) {
            obj.push(parse(input, type, dim - 1, false));
        }
        if (checkAssert) {
            typeCheck(obj, type, dim);
        }
        return obj;
    } else {
        var obj = parse0d(input.shift(), type);
        if (checkAssert) {
            typeCheck(obj, type, dim);
        }
        return obj;
    }
}

function assertAfterInput(input) {
    if (input.length > 0) throw new Error('after parse error: input is not empty');
}

function read(rl, callback) {
    var input = [];
    rl.on('line', function (line) {
        input.push(line);
    })
    .on('close', function () {
        callback(input);
    });
}

const fs = require('fs');

function write(outputStream, result, type, dim, checkAssert = true) {
    if (dim < 0) throw new Error('write error: dim is negative');
    if (checkAssert) typeCheck(result, type, dim);
    if (dim > 0) {
        fs.writeSync(outputStream, result.length + '\n');
        for (var i = 0; i < result.length; ++i) {
            write(outputStream, result[i], type, dim - 1, false);
        }
    } else {
        fs.writeSync(outputStream, result + '\n');
    }
}

module.exports = {
    read,
    write,
    parse,
}