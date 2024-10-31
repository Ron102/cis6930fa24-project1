
  

  

  

# cis6930fa24 -- Project 1 --

  

  

  

**Name: Ronit Bali**

**UFID - 58455645**

  

  

  

# Assignment Description

  

  

  

This is my project 1 submission. I have designed a system that accepts plain text documents and detects and censors/redacts “sensitive” information by replacing them with the Unicode full block character █ (U+2588). The program will censor all _names_, _dates_, _phone numbers_, _addresses_ and _concepts_, and print the redacted files with `.censored` extension. The flag `--concept` asks the system to redact all portions of text that have anything to do with a particular concept.

```

pipenv run python redactor.py --input '*.txt' \

--names --dates --phones --address\

--concept 'kids' \

--output 'files/' \

--stats stderr

```

  

# How to install and use

  

To install all the dependencies:

  

```

pipenv install

```

  

To activate the virtual environment:

  

```

pipenv shell

```

  
  

To run the program, run the _redactor.py_ program using:

  

```

pipenv run python redactor.py --input '[folder_path]/*.txt'

--names --dates --phones --address

--concept

--output '[folder_path]/*.txt'

--stats [stderr, stdout, filename]

```

To test the program functionalities:

```

pipenv run python -m pytest

```

  

  

## Flags

  

-  `--input` : This parameter takes a _glob_ that represents the files that can be accepted. More than one input flag may be used to specify groups of files. If a file is not able to be read or censored, then an error message is displayed.

-  `--names` corresponds to any type of name (proper nouns)

-  `--dates` correspond to any written dates (4/9/2025, April 9th, 22/2/22)

-  `--phones` describes any phone number in its various forms.

-  `--address` corresponds to any physical (postal) address (not e-mail address).

-  `--concept` corresponds to a word or phrase that represents a concept. A concept is either an idea or theme. Any section of the input files that refer to this concept are redacted. I have redacted the words/sentences based on the words related to the concept word, such as synonyms. Any sentence describing an idea having the related word will get redacted.

-  `--output` specifies a directory to store all the censored files. Example: `--output 'folder/'`: files will be written to this folder with a `.censored` extension.

-  `--stats` corresponds to the output file path, written to either `stderr`, `stdout` or `filename`.

  

## Functions

  

#### redactor.py

  

*main()* - This function calls the _arg_pass()_ function and passes the arguments entered to the _fileprocessor()_ function

  

_arg_pass()_ - This function accepts command-line arguments for each flag as mentioned in the problem statement. All flags are mandatory, and the input and concept flags can be used multiple times.


*fetch_synonyms(concept)* - This function uses nltk to fetch the synonyms of the concept(s)


  *derivational_forms()* - This function includes the derivational forms of the concepts. For example, if the concept is *love*, then sentences having words such as *loving, loved, loves, lovely etc* should also be redacted.


*sentence_redact(content, concepts, entity_counts)* - This function redacts sentences having the concept(s) related words in them.

  
*redact_addresses(content, entity_counts)* - This function uses the _usaddress_ library to detect US based addresses and redacts them. The spaces/symbols between addresses are not redacted.


*redact_content()* - This function uses regex to identify the patterns of mobile, email and name patterns. The emails contain sections called X_Folder and X_Origin, which contains names of people sending the emails. These identified texts are then redacted.


*fileprocessor()* - This function inputs arguments from arg_parse() and uses the redact_content() function to redact contents. It also deals with the stderr and stdout arg stats, and checks if the file path/glob pattern is correct/found, and uses the en_core_web_trf package from spacy-transformers to get statistics of each individual file by counting the number of instances of each flag, writing it to a file specified by output or stdout or stderr.

  

#### test_names.py

Test file which takes a sample name and verifies it against the redacted correct output.

  

#### test_dates.py

Test file which takes a sample date and verifies it against the redacted correct output (includes time as well).

  

#### test_phones.py

Test file which takes a sample phone number and verifies it against the redacted correct output.

  

#### test_concepts.py

Test file which takes a sample concept and verifies it against the redacted correct output.

  

#### test_address.py

Test file which takes a sample address and verifies it against the redacted correct output.

  

  

## Bugs and Assumptions

  

Some bugs and assumptions can be encountered/should be kept in mind while executing the program:

  

- The program will ONLY work for English language. No other languages are "yet" supported.

- Usage of correct flags is mandatory, as using incorrect flags/not using required flags could hamper the execution of the program.

- The program may not be fully sufficient to censor all the sensitive information, especially _concepts_. Redacting concepts is somewhat vague and subjective, and thus my understanding of censoring any concept(s) might differ from others.
- The model used in the program is *en_core_web_trf*, which is a transformers model. While the model is more accurate, it requires more time and resources to execute. 

- The program might run slow for a large number of files, as it has to use SpaCy and other libraries to analyze the entire files and generated censored ones.

- The program might not execute completely if the output directory is incorrect/doesn't exist.