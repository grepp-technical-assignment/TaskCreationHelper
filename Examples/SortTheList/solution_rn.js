function solution(arr) {
    arr.sort((a, b) => a - b);
    return arr;
}

module.exports = { // for testing (v1) //
    solution,
}