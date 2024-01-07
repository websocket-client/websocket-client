# Contributing

Hello :wave: and thank you for contributing! :tada:

Before you contribute, please take a minute to review the contribution process
based on what you want to do.

## I got an error or I have a question

Great! We are happy to help. Before you ask your question, please check if your
question can be answered from the following 5 steps:
- [ ] The [project documentation examples](https://websocket-client.readthedocs.io/en/latest/examples.html)
- [ ] The [project documentation FAQ](https://websocket-client.readthedocs.io/en/latest/faq.html)
- [ ] Search for your question in [old existing issues](https://github.com/websocket-client/websocket-client/issues)
- [ ] If you encountered an error message, try googling the error message and see if you find an answer
- [ ] Check if the same issue exists if you uninstall the websocket-client
library on your system (using `pip uninstall websocket-client`) and install the
[latest master branch](https://github.com/websocket-client/websocket-client)
directly from a clone of the repository by using `pip install -e .`
(see [installation info](https://github.com/websocket-client/websocket-client#installation))

If you did not get your question answered from these 5 steps, then please open a
new issue and ask your question! When you explain your problem, please:
- [ ] [Enable the tracing feature](https://websocket-client.readthedocs.io/en/latest/examples.html#debug-and-logging-options)
and include the entire debug trace of your connection process in the issue
- [ ] Provide a [minimum reproducible example](https://stackoverflow.com/help/minimal-reproducible-example)
program to allow other users to recreate and demonstrate the error
- [ ] Add an explanation for what you are trying to accomplish. If you can
provide your code (or example code) in the issue, this helps a lot!

## I have a suggestion or idea

Great! Please make a new issue an explain your idea, but first do a quick search
in [old existing issues](https://github.com/websocket-client/websocket-client/issues)
to see if someone already proposed the same idea.

## I want to contribute code

Great! In your pull request (PR), please explain:
1. What is the problem with the current code
2. How your changes make it better
3. Provide some example code that can allow someone else to recreate the
problem with the current code and test your solution (if possible to recreate).

## I want to contribute documentation

Great! To edit the [project documentation](https://websocket-client.readthedocs.io),
it is recommended that you install Sphinx and build the updated documentation
locally before submitting your edits. The Sphinx dependencies can be
installed with `pip install websocket-client[docs]`. To build a new version of the documentation,
change directories (or `cd`) to the `docs/` directory and run `make clean html`.
Any build warnings or errors will be displayed in your terminal, and the new
documentation will then be available in the `docs/build/html/` directory.
You may also find the
[Sphinx documentation style guide](https://documentation-style-guide-sphinx.readthedocs.io/en/latest/style-guide.html)
useful when editing reStructuredText (reST), which is quite
different from Markdown.
