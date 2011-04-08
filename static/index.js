var SearchController = Class.create({
  BASE_URL: "http://docs.python.org/",

  initialize: function(input_element, results_element) {
    this.input_element = input_element;
    this.results_element = results_element;

    // Listen for key events on the input box.
    this.input_element.observe('keyup', this.input_changed.bind(this));

    // Listen for key events on everything.
    document.observe('keyup', this.key_pressed.bind(this));

    // Fill the results list initially
    this.search("");
  },

  input_changed: function(event) {
    this.search(this.input_element.value);
  },

  search: function(search_text) {
    var html = "";
    this.results = [];
    this.selected_result = -1;

    var matches = 0;
    var len = data.length;
    for (var i=0 ; i<len && matches<500 ; ++i) {
      // Does it match the search text?
      if (!data[i][0].startsWith(search_text))
        continue;

      // Get information about this symbol
      var result = {
        name:        data[i][0],
        type:        data[i][1],
        destination: data[i][2],
      };

      result.anchor = result.name;
      if (result.type == "mod") {
        result.anchor = "module-" + result.name;
      }

      // Construct the URL
      result.url = this.BASE_URL + result.destination + '#' + result.anchor;

      // Add to the list of results
      this.results.push(result);
      ++matches;

      // Add to the HTML
      html += '<li class="' + result.type + '">' +
              '<a target="content1" href="' + result.url + '">' +
              result.name + '</a></li>';
    }

    // Make the list and insert it into the DOM
    var ul = new Element("ul");
    ul.innerHTML = html;
    ul.observe('click', this.result_clicked.bind(this));

    this.results_element.update(ul);
  },

  result_clicked: function(event) {
    var item = event.findElement("li");
    if (item == document)
      return;

    var a = item.select("a")[0];
    $("content1").src = a.href;
  },

  key_pressed: function(event) {
    switch (event.keyCode) {
      case Event.KEY_UP:
        this.move_selection(-1);
        break;
      case Event.KEY_DOWN:
        this.move_selection(+1);
        break;
    }
  },

  move_selection: function(delta) {
    if (this.selected_result == -1) {
      this.selected_result = 0;
    } else {
      // Deselect the old selection
      var element = 
    }
  }
});

var controller;
Event.observe(window, 'load', function() {
  controller = new SearchController($("search"), $("searchresults"));
});
