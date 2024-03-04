/**
 * main process
 */
window.onload = function() {
    var logo = document.querySelector('#logo');
    logo.onclick = function() {
        window.location.href = './report.html';
    }
    
    drawTable();
    addEvent();
}

/**
 * Draw report table
 */
 function drawTable() {
    function makeItem(data, tag = 'span') {
        var item = document.createElement(tag);
        item.textContent = data;
        return item;
    }
    function makeLine(data, tag) {
        var line = document.createElement('tr');
        for (var i = 0; i < data.length; ++i) {
            var cell = document.createElement(tag);
            cell.appendChild(makeItem(data[i]));
            line.appendChild(cell);
        }
        return line;
    }
    var thead = document.querySelector('#tch-table thead');
    var tbody = document.querySelector('#tch-table tbody');
    var headFrag = new DocumentFragment();
    var bodyFrag = new DocumentFragment();

    // parse data //
    var solutions = window.__TCH__data.map(data => data.solution);
    var verdicts = window.__TCH__data.map(data => data.verdict);
    var distributions = window.__TCH__data.map(data => data.distribution);
    var pdata = [];
    var vlen = verdicts[0] ? verdicts[0].length : 0;
    for (var i = 0; i < vlen; ++i) {
        pdata.push([]);
        for (var j = 0; j < verdicts.length; ++j) {
            pdata[i].push(`${verdicts[j][i]} (${String(distributions[j][i]).substring(0, 7)}s)`);
        }
    }
    pdata.push([]);
    for (var i = 0; i < verdicts.length; ++i) {
        var cnt = verdicts[i].reduce((acc, v) => v == 'AC' ? acc + 1 : acc, 0);
        pdata[vlen].push(`(${cnt} / ${vlen})`)
    }

    headFrag.appendChild(makeLine(['#'].concat(solutions), 'th'));
    for (var i = 0; i < pdata.length; ++i) {
        bodyFrag.appendChild(makeLine([i+1].concat(pdata[i]), 'td'));
    }

    // draw //
    thead.innerHTML = '';
    tbody.innerHTML = '';
    thead.appendChild(headFrag);
    tbody.appendChild(bodyFrag);
}

/**
 * add click event
 */
function addEvent() {
    var line = document.querySelectorAll('#tch-table tbody tr:not(:last-child)');
    for (var i = 0; i < line.length; ++i) {
        var cells = line[i].querySelectorAll('td:not(:first-child) span');
        for (var j = 0; j < cells.length; ++j) {
            var cell = cells[j];
            cell.classList.add('clickable');
            cell.onclick = (function (i, j) {
                return function(e) {
                    window.location.href = (j + 1) + '/detail' + (i + 1) + '.html';
                }
            })(i, j);
        }
    }
}