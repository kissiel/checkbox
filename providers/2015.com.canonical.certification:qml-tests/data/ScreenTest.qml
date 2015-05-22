import QtQuick 2.0
import Ubuntu.Components 1.1
import QtQuick.Window 2.0

Page {
    anchors.fill: parent
    id: screenTest

    signal fieldClicked(var row, var col);
    signal allTargetsHit;
    signal tripleClicked;

    property var resolution: 20


    function addTarget(target) {
        _targets.push(target);
    }
    function addRandomTargets(count) {
        for (var i = 0; i < count; i++) {
            var randomField = {
                "x": Math.floor(Math.random() * _grid.cols),
                "y": Math.floor(Math.random() * _grid.rows)}
            addTarget(randomField);
        }
    }


    function addEdge(edgeName) {
        switch(edgeName) {
        case "top":
            for(var i = 0; i < _grid.cols; i++) addTarget({"x": i, "y": 0});
            break;
        case "bottom":
            for(var i = 0; i < _grid.cols; i++) addTarget({"x": i, "y": _grid.rows-1});
            break;
        case "left":
            for(var i = 0; i < _grid.rows; i++) addTarget({"x": 0, "y": i});
            break;
        case"right":
            for(var i = 0; i < _grid.rows; i++) addTarget({"x": _grid.cols-1, "y": i});
            break;
        }
    }

    function runTest() {
        var currentTarget = _targets.shift();
        var col = currentTarget.x;
        var row = currentTarget.y;

        //create component
        var fieldComponentName = "touchField-" + row.toString() + "x" + col.toString();
        var currentField = Qt.createQmlObject(_touchFieldDefinition, screenTest, fieldComponentName);
        currentField.width = _grid.fieldWidth;
        currentField.height = _grid.fieldHeight;
        currentField.x = _grid.fieldWidth*col;
        currentField.y = _grid.fieldHeight*row;
        currentField.color = "blue";
        _grid[row][col].component = currentField

        fieldClicked.connect(function(row, col) {
            if(row === currentTarget.y && col === currentTarget.x) {
                //disconnect self, so we don't activate ALL next fields while touching the current one
                fieldClicked.disconnect(arguments.callee);
                _grid[row][col].component.color = "grey";
                if(_targets.length === 0) {
                    allTargetsHit();
                } else {
                    runTest(_targets);
                }
            }
        });
    }

    MultiPointTouchArea {
        anchors.fill: parent
        mouseEnabled: true
        Timer {
            id: tripleClickTimeout
            interval: 400

            property var clickCount: 0
            onTriggered: {
                clickCount = 0;
                stop();
            }
        }

        onPressed: {
            touchUpdated(touchPoints)
            if (!tripleClickTimeout.running) tripleClickTimeout.start();
            tripleClickTimeout.restart();
            if (tripleClickTimeout.clickCount++ > 2) {
                tripleClicked();
                tripleClickTimeout.stop();
                tripleClickTimeout.clickCount = 0;
            }
        }

        onTouchUpdated: {
            for (var i in touchPoints) {
                _grid.click(touchPoints[i].x, touchPoints[i].y);
            }
        }
    }

    Component.onCompleted: {
        _grid = _createGrid(resolution);
    }

    function _createGrid(resolution) {
        var _grid = {};
        _grid.cols = Math.round(resolution*(width/height));
        _grid.rows = resolution;
        _grid.fieldWidth = width/_grid.cols;
        _grid.fieldHeight = height/_grid.rows;
        for (var row = 0; row<_grid.rows; row++) {
            _grid[row] = {};
            for (var col = 0; col<_grid.cols; col++) {
                _grid[row][col] = {};
                _grid[row][col].label = row.toString() + "x" + col.toString();
                _grid[row][col].multi = row*col;
            }
        }
        _grid.click = function(x, y) {
            //compute idecies of the field from page coords
            var col = Math.floor(x / _grid.fieldWidth);
            var row = Math.floor(y / _grid.fieldHeight);
            fieldClicked(row, col)
        }

        return _grid;
    }

    property var _grid
    property var _targets: [];
    property var _touchFieldDefinition: "
    import QtQuick 2.0
        Rectangle {
            id: rectangle
            radius: 0.2 * width
        }
    "
}
