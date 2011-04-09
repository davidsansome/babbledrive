var SearchController = Class.create({
  BASE_URL: "static/doc/2.7.1/",

  initialize: function(input_element, results_element, content_element, header_element) {
    this.input_element = input_element;
    this.results_element = results_element;
    this.content_element = content_element;
    this.header_element = header_element;

    this.ignore_next_hash_change = false;

    // Listen for key events on the input box.
    this.input_element.observe('keyup', this.input_changed.bind(this));

    // Listen for key events on everything.
    document.observe('keydown', this.key_pressed.bind(this));

    // Listen for an event when the frame's URL changes.
    this.content_element.observe('load', this.content_frame_changed.bind(this));
    this.content_frame_changed();

    // Browse to the page the user put in the hash part of the URL.
    if (window.location.hash) {
      this.browse_to(window.location.hash);
      this.activate_selection();
    } else {
      this.search("");
    }

    this.input_element.focus();
  },

  input_changed: function(event) {
    this.search(this.input_element.value, true);
  },

  search: function(search_text, highlight) {
    // Don't do anything if the text wasn't changed since last time.
    if (search_text == this.search_text)
      return;
    this.search_text = search_text;

    // Split the text into tokens, ignoring empty ones.
    var tokens = search_text.toLowerCase().split(" ").reject(function(x) { return x.blank(); });
    var tokens_len = tokens.length;

    // This regex will highlight the search terms in the matches.
    var highlight_regexp = new RegExp("(" + tokens.join("|") + ")", "gi");

    var html = ["", "", "", ""];
    this.result_count = 0;
    this.selected_result = -1;

    var len = data.length;
    for (var i=0 ; i<len && this.result_count<500 ; ++i) {
      var result_name_lower = data[i][0];

      // Does it match the search text?
      // The rules are:
      //  * If any token isn't found in the symbol name, abort.
      //  * Otherwise, for each token increment the score by:
      //     +2 if the match was at the beginning or after a period
      //     +1 if the case matched exactly
      var token_didnt_match = false;
      var overall_score = 0;

      if (tokens.length > 0) {
        for (var j=0 ; j<tokens_len ; ++j) {
          var index = result_name_lower.indexOf(tokens[j]);
          if (index == -1) {
            // If it didn't match at all then short circuit the scoring and
            // skip the other tokens.
            token_didnt_match = true;
            break;
          }

          var score = 0;

          // Matched at the beginning or after a period?
          if (index == 0 || result_name_lower.charAt(index-1) == '.') {
            score += 2;
          }

          // Case matched?
          if (data[i][1].substring(index, index + tokens[j].length) == tokens[j]) {
            score += 1;
          }

          overall_score = Math.max(overall_score, score);
        }

        // Didn't match?
        if (token_didnt_match)
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
      if (highlight && tokens.length != 0) {
        highlighted_name = highlighted_name.replace(
          highlight_regexp, '<span class="highlight">$1</span>');
      }

      // Construct the URL
      result.url = this.BASE_URL + result.destination + '#' + result.anchor;

      // Add to the list of results
      ++this.result_count;

      // Add to the HTML
      html[overall_score] += '<li class="' + result.type + '">' +
                             '<a target="contentframe" href="' + result.url + '">' +
                             highlighted_name + '</a></li>';
    }

    // Make the list and insert it into the DOM
    var ul = new Element("ul");
    ul.innerHTML = html[3] + html[2] + html[1] + html[0];
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
    if (event.altKey || event.ctrlKey)
      return;

    var element = Event.findElement(event);

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
        if (event.keyCode >= 65 && event.keyCode <= 90 && element != this.input_element) {
          var char = String.fromCharCode(event.keyCode);
          if (!event.shiftKey)
            char = char.toLowerCase();

          // Stop the event before focusing the input box or it'll be added
          // twice.
          Event.stop(event);
          this.input_element.value += char;
          this.input_element.focus();
        }
        return;
    }

    Event.stop(event);
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
    this.ignore_next_hash_change = true;
    this.content_element.src = li.select("a")[0].href;
  },

  content_frame_changed: function(event) {
    var frame_window = this.content_element.contentWindow;
    var frame_document = frame_window.document;

    // Update the title
    var title = frame_document.title;
    this.header_element.update(title.escapeHTML());
    document.title = title;

    // Listen for keypresses on the new frame
    Event.observe(frame_document, 'keydown', this.key_pressed.bind(this));

    // Listen for hash changes
    Event.observe(frame_window, 'hashchange', this.content_hash_changed.bind(this));
    this.content_hash_changed();
  },

  content_hash_changed: function(event) {
    var name = this.content_element.contentWindow.location.hash;
    if (!name)
      return;

    // Take any module- prefix off module names.
    if (name.startsWith("#module-"))
      name = "#" + name.substring(8);

    window.history.replaceState(name, "", name);

    if (this.ignore_next_hash_change) {
      this.ignore_next_hash_change = false;
      return;
    }

    this.browse_to(name);
  },

  browse_to: function(name) {
    // Take the # off
    name = name.substring(1);

    // Find the top-level symbol name.
    var top_level_symbol = name;
    if (top_level_symbol.indexOf(".") != -1)
      top_level_symbol = top_level_symbol.substring(0, top_level_symbol.indexOf("."));

    // Try to find a documentation entry with this name
    var len = data.length;
    for (var i=0 ; i<len ; ++i) {
      if (data[i][1] != name)
        continue;

      // Got one - do a search for the top-level symbol
      this.search(top_level_symbol, false);

      // Now select the right search result
      var results = this.results_element.select("li");
      var results_len = results.length;
      for (var j=0 ; j<results_len ; ++j) {
        if (results[j].down().innerText == name) {
          this.set_selection(j);
          break;
        }
      }

      break;
    }
  }
});

var controller;
Event.observe(window, 'load', function() {
  controller = new SearchController(
    $("search"), $("searchresults"), $("contentframe"), $("contentheader"));
});
