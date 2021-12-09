function solution(d0, d1, d2) {
    var result = d0;
    for (var i = d1.length; i--; ) {
        result += d1[i];
    }
    for (var i = d2.length; i--; ) {
        var ival = d2[i]
        for (var j = ival.length; j--; ) {
            result += ival[j];
        }
    }
    return result;
}