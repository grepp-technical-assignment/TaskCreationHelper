/**
 * main process
 */
window.onload = function() {
    var logo = document.querySelector('#logo');
    logo.onclick = function() {
        window.location.href = '../report.html';
    }

    drawResult();
    addEvent();
}

/**
 * draw result
 */
function drawResult() {
    function makeCorrectWord(txt) {
        var correct = document.createElement('div');
        correct.className = 'tch-correct';
        correct.textContent = txt;
        return correct;
    }
    function makeWrongWord(txt1, txt2) {
        var wrong = document.createElement('div');
        wrong.className = 'tch-wrong';
        wrong.textContent = `cpu(${txt1}) ans(${txt2})`;
        return wrong;
    }
    function makeCmpResult(txt1, txt2) {
        var res = [];
        var len = txt1.length > txt2.length ? txt1.length : txt2.length;
        for (var i = 0; i < len; ++i) {
            var val1 = i < txt1.length ? txt1[i] : '';
            var val2 = i < txt2.length ? txt2[i] : '';
            if (val1 == val2) {
                res.push(makeCorrectWord(val1));
            } else {
                res.push(makeWrongWord(val1, val2));
            }
        }
        return res;
    }
    function appendChildren(parent, children) {
        var frag = new DocumentFragment();
        for (var i = 0; i < children.length; ++i) {
            frag.appendChild(children[i]);
        }
        parent.appendChild(frag);
    }
    function tokenize(txt) {
        var reg = /,|\s|\[|\]/g;
        var spt = txt.split(reg);
        return spt.filter(s => s.length > 0);
    }

    var result = document.querySelector('#tch-result');
    var cpData = document.querySelector('#tch-cp-data');
    var cfData = document.querySelector('#tch-cf-data');
    var rawData = document.querySelector('#tch-raw-data');

    var raw = tokenize(window.__TCH__tcData);
    var compressed = tokenize(window.__TCH__tcData.substring(0, 100));
    var ans = tokenize(window.__TCH__acData);
    var cans = tokenize(window.__TCH__acData.substring(0, 100));

    result.textContent = 'Result: ' + (window.__TCH__isAC ? 'AC' : window.__TCH__isFail ? 'FAIL' : 'WA');

    appendChildren(cpData, makeCmpResult(compressed, cans));
    appendChildren(cfData, 
        makeCmpResult(raw, ans)
            .map((word, idx) => {
                word.textContent = `[${idx}] ${word.textContent}`;
                return word;
            })
            .filter(word => word.className == 'tch-wrong')
    );
    appendChildren(rawData, makeCmpResult(raw, ans));
}

/**
 * Add Event Listener
 */
function addEvent() {
    var cfBtn = document.querySelector('#tch-cf-btn');
    var rawBtn = document.querySelector('#tch-raw-btn');

    cfBtn.onclick = function() {
        var cf = document.querySelector('#tch-cf-data');
        cf.style.display = 'block';
    }
    rawBtn.onclick = function() {
        var raw = document.querySelector('#tch-raw-data');
        raw.style.display = 'block';
    }
}