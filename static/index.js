var SearchController = Class.create({
  BASE_URL: "http://docs.python.org/",

  initialize: function(input_element, results_element) {
    this.input_element = input_element;
    this.results_element = results_element;

    // Listen for key events on the input box.
    this.input_element.observe('keyup', this.input_changed.bind(this));

    // Listen for key events on everything.
    document.observe('keydown', this.key_pressed.bind(this));

    // Fill the results list initially
    this.search("");
  },

  input_changed: function(event) {
    this.search(this.input_element.value);
  },

  search: function(search_text) {
    // Don't do anything if the text wasn't changed since last time.
    if (search_text == this.search_text)
      return;
    this.search_text = search_text;

    // Split the text into tokens, ignoring empty ones.
    var tokens = search_text.toLowerCase().split(" ").reject(function(x) { return x.blank(); });
    var tokens_len = tokens.length;

    // This regex will highlight the search terms in the matches.
    var highlight_regexp = new RegExp("(" + tokens.join("|") + ")", "gi");

    var html = ["", ""];
    this.result_count = 0;
    this.selected_result = -1;

    var len = data.length;
    for (var i=0 ; i<len && this.result_count<500 ; ++i) {
      var result_name_lower = data[i][0];

      // Does it match the search text?  We want to sort things that match at
      // the beginning of the string first, so match_type values mean:
      //  -1 - not at all
      //   0 - at the beginning
      //   1 - at the end
      var match_type = -1;

      if (tokens.length == 0) {
        // If there are no search tokens then display everything.
        match_type = 0;
      } else {
        for (var j=0 ; j<tokens_len ; ++j) {
          var index = result_name_lower.indexOf(tokens[j]);
          if (index == -1) {
            match_type = -1;
            break;
          } else if (index == 0) {
            match_type = 0;
          } else if (match_type != 0) {
            match_type = 1;
          }
        }

        // Didn't match?
        if (match_type == -1)
          continue;
      }

      // Get information about this symbol
      var result = {
        name:        data[i][1],
        type:        data[i][2],
        destination: data[i][3],
      };

      result.anchor = result.name;
      if (result.type == "mod") {
        result.anchor = "module-" + result.name;
      }

      // Highlight the search terms in the result
      var highlighted_name = result.name;
      if (tokens.length != 0) {
        highlighted_name = highlighted_name.replace(
          highlight_regexp, '<span class="highlight">$1</span>');
      }

      // Construct the URL
      result.url = this.BASE_URL + result.destination + '#' + result.anchor;

      // Add to the list of results
      ++this.result_count;

      // Add to the HTML
      html[match_type] += '<li class="' + result.type + '">' +
                          '<a target="content1" href="' + result.url + '">' +
                          highlighted_name + '</a></li>';
    }

    // Make the list and insert it into the DOM
    var ul = new Element("ul");
    ul.innerHTML = html[0] + html[1];
    ul.observe('click', this.result_clicked.bind(this));

    this.results_element.update(ul);
  },

  result_clicked: function(event) {
    var li = event.findElement("li");
    if (li == document)
      return;

    this.set_selection(this.get_result_index(li));
    this.activate_li(li);
  },

  key_pressed: function(event) {
    switch (event.keyCode) {
      case Event.KEY_UP:
        this.move_selection(-1);
        break;

      case Event.KEY_DOWN:
        this.move_selection(+1);
        break;

      case Event.KEY_RETURN:
        this.activate_selection();
        break;

      case Event.KEY_ESC:
        this.input_element.focus();
        this.input_element.select();
        break;

      default:
        return;
    }

    event.stop();
  },

  get_result_li: function(index) {
    return this.results_element.select("li")[index];
  },

  get_result_index: function(li) {
    var all = this.results_element.select("li");
    var len = all.length;
    for (var i=0 ; i<len ; ++i) {
      if (all[i] == li)
        return i;
    }
    return null;
  },

  move_selection: function(delta) {
    if (this.selected_result == -1) {
      this.set_selection(0);
    } else {
      this.set_selection(this.selected_result + delta);
    }
  },

  set_selection: function(index) {
    if (this.result_count == 0)
      return;

    if (this.selected_result != -1) {
      // Deselect the old element
      var element = this.get_result_li(this.selected_result);
      element.removeClassName("selected");
    }

    // Restrict the selection to the size of the result set
    index = Math.max(0, Math.min(this.result_count-1, index));

    // Select the new element
    var element = this.get_result_li(index);
    element.addClassName("selected");

    this.selected_result = index;
  },

  activate_selection: function() {
    if (this.selected_result == -1) {
      this.move_selection(+1);
      if (this.selected_result == -1)
        return;
    }

    this.activate_li(this.get_result_li(this.selected_result));
  },

  activate_li: function(li) {
    var a = li.select("a")[0];
    $("content1").src = a.href;
  },
});

var controller;
Event.observe(window, 'load', function() {
  controller = new SearchController($("search"), $("searchresults"));
});
