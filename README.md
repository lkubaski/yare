Yet Another Forward Chaining Rule Engine
====

Python [Forward Chaining Rule Engine](https://en.wikipedia.org/wiki/Forward_chaining) (aka Inference Engine, aka Expert System) with support for:
* adding or removing facts when executing rules
* parametric rules aka "using variables in rules"
* callback functions

I wrote this to educate myself on rule engines. 
I also wanted the configuration file to be easily understandable by non-developers

# 1. Configuration file

## 1.1. A simple configuration file

Before explaining how to create a configuration file, let's see what a basic configuration file looks like.

```ini
[rules]
rule1: apple('golden') => add:fruit('golden')
rule2: fruit('golden') => add:eatable('golden')

[facts]
apple('golden')

[goal]
eatable('golden')
```

As explained further below, rules can also contain variables, meaning that this configuration file achieves the same goal while
also being more generic:

```ini
[rules]
rule1: apple(X) => add:fruit(X)
rule2: fruit(X) => add:eatable(X)

[facts]
apple('golden')

[goal]
eatable('golden')
```

## 1.2 The [rules] section

A rule has this format: `[RULE_NAME]: [LEFT_EXPRESSION] => [RIGHT_EXPRESSION]`

### 1.2.1 rule [LEFT_EXPRESSION] format

The `[LEFT_EXPRESSION]` is a python expression which consists of predicates and operators. 
* a predicate is similar to a function invocation in python: the predicate values can be string literals (like 'apple') or string variables (like X)
* supported operators are 'and', 'not', '==' and '!='

Here are some examples of left expressions:
* `apple('golden')`
* `apple('golden') and apple('gala')`
* `apple('golden') and not banana('cavendish')`
* `parent(X,Y) and parent(X,Z) and Y!=Z`

### 1.2.2 rule [RIGHT_EXPRESSION] format

The `[RIGHT_EXPRESSION]` is a comma separated list of actions that are executed when the `[LEFT_EXPRESSION]` evaluates to 'True'. There are 3 different type of actions:
* `add:[fact]` -> adds a fact to the knowledge base
* `remove:[fact]` -> removes a fact from the knowledge base
* `function:[function]` -> invokes a callback

Here are some examples of right expressions:
* `add:fruit('golden')`
* `add:position(X), remove:position(Y), function:my_function(X,Y)`

### 1.2.3 Putting it all together

Let's use this rule as an example: `rule1: parent(A,B) and parent(B,C) => add:grand_parent(A,C), function:my_function(A,C)`
* The rule is fired when the knowledge base contains a `parent(A,B)` fact and a `parent(B,C)` fact
  * So for example, the rule is fired when the knowledge base contains a `parent('bob', 'peter')` fact and a `parent('peter','john')'` fact
  * Notice that the variable B is used 2 times in the left expression so the value of that variable needs to be the same in both predicates (in this example, the value is `'peter'`)
* when the rules is fired, 2 things happen:
  * 1: The `add:grand_parent(A,C)` action is executed, which adds a `grand_parent('bob','john')` fact to the knowledge base (the A & C variables are replaced with the values that were used to fire the rule)
    * That new fact can then potentially fire additional rules containing a left expression like `grand_parent(A,B)` or `grand_parent('bob',A)` or `grand_parent(A,'john')` or `grand_parent('bob','john')`
  * 2: The `function:my_function(A,C)` action is executed, which invokes the python function `my_function` with 2 parameters: `'bob'` & `'john'`

## 1.3. The [facts] section

A list of facts - one on each line - that are initially added to the knowledge base to bootstrap the rule engine. 
* To add a fact to the knowledge base when a rule is fired, use a `add:[fact]` action in the rule right expression
* To remove a fact from the knowledge base when a rule is fired, use a `remove:[fact]` action in the rule right expression
* A fact cannot contain variables, meaning that `fruit('apple')` is a valid fact but `fruit(X)` is not -> variables can only be used in rules.

## 1.4. The [goal] section

When there are no more rules to evaluate, the rule engine checks if the specific goal is in the knowledge base and returns 'True' or 'False'
* A goal is actually a fact, meaning that it also cannot contain variables

## 1.5. A more advanced configuration file

```ini
[rules]
rule1: man(A) and parent(A,B) => add:father(A,B)
rule2: woman(A) and parent(A,B) => add:mother(A,B)
rule3: man(A) and parent(B,A) => add:son(A,B)
rule4: woman(A) and parent(B,A) => add:daughter(A,B)
rule5: son(A,B) => add:child(A,B)
rule6: daughter(A,B) => add:child(A,B)
rule7: parent(A,B) and parent(A,C) and B!=C => add:siblings(B,C)
rule8: parent(A,B) and parent(B,C) => add:grand_parent(A,C)
rule9: woman(A) and grand_parent(A,B) => add:grand_mother(A,B)
rule10: man(A) and grand_parent(A,B) => add:grand_father(A,B)

[facts]
man('george')
man('larry')
man('peter')
woman('sophia')
woman('jacqueline')
woman('catherine')
parent('george','larry')
parent('george','sophia')
parent('jacqueline','larry')
parent('jacqueline','sophia')
parent('peter','jacqueline')
parent('catherine','jacqueline')

[goal]
siblings('larry', 'sophia')
```

# 2. How the engine works

Here is a high level description of how the rule engine works:
* The engine goes through all the rules in the order they're defined in the configuration rule
* For each rule, the engine finds all the combination of facts that allow the left expression to evaluate to 'True' 
* For each combination of those facts:
   * all the actions in the right expression are processed
   * IF any of those actions adds or removes facts to/from the knowledge base, the engine starts evaluating rules from the beginning again
* Finally, when there are not more rules to evaluate, the engine checks if the goal matches a fact in the knowledge base

# 3. Additional notes
* Once a rule has fired for a combination of facts, the rule won't be evaluated for that same combination of facts UNLESS one of those facts is removed and added again to the knowledge base
* To better understand how the engine works, look at the unit tests in the /test folder and the sample configuration files in the /config folder

# 4. Known limitations
* The predicates used in a rule left expression only support string literals or string variables: other types - like integers - are not supported
* "or" statements are not supported in the rules left expressions: the workaround is simply to create two rules - one for each condition - instead of one.
* There is no protection against infinite loops (see the sample configuration files in the /config folder to see when this can happen)

# 5. Other Python rule engines on Github (non exhaustive list)
* https://github.com/noxdafox/clipspy
* https://github.com/zeroSteiner/rule-engine
* https://github.com/santalvarez/python-rule-engine
* https://github.com/blurg/sauron-engine
* https://github.com/jeyabalajis/simple-rule-engine
* https://github.com/saurabh0719/py-rules-engine
* https://github.com/jruizgit/rules (aka "Durable Rules Engine")
* https://github.com/nilp0inter/experta
* https://github.com/nemonik/Intellect
* https://maif.github.io/arta/
* https://github.com/venmo/business-rules