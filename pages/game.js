{
  class BullsNCows {
    #fourBulls;
    constructor() {
      this.#fourBulls = generateRandomNumber();
    }
    _checkGuess(guess) {
      return checkGuess(this.#fourBulls, guess);
    }
  }

  let game = new BullsNCows();
  // const DEFAULT_GUESS_LENGTH = 4;

  // generate random numbers with unique digits
  function generateRandomNumber(digits = 4) {
    // digits: cannot be more than 10

    // between 0 and 1 (can't ne one)
    // between 0 and 9 (both inclusive)
    if (digits > 10) {
      // TODO validation at input also
      return;
    }
    const numArr = [];
    numArr.push(Math.floor(Math.random() * 10));

    while (numArr.length < digits) {
      let newNum = Math.floor(Math.random() * 10);
      while (numArr.indexOf(newNum) > -1) {
        newNum = Math.floor(Math.random() * 10);
      }
      numArr.push(newNum);
    }
    return numArr.join("");
  }

  let correctGuess = false;

  const playAnother = document.getElementById("play-another");
  const pastGuesses = document.getElementById("past-guesses");
  const guessForm = document.getElementById("guess");
  const guessInput = document.getElementById("guess-input");
  const guessTooltip = document.getElementById("guess-tooltip");

  playAnother.addEventListener("click", function (event) {
    while (pastGuesses.firstChild) {
      guessForm.classList.remove("hidden");
      pastGuesses.removeChild(pastGuesses.lastChild);
      correctGuess = false;
      game = new BullsNCows();
    }
  });

  const fourDigitNumRegex = /^(?!.*(.).*\1)\d{4}$/;
  guessForm.addEventListener("submit", function (event) {
    event.preventDefault();

    if (fourDigitNumRegex.test(guessInput.value)) {
      // 👆🏽 simple validation
      const guessCheckResult = game._checkGuess(guessInput.value);
      if (guessCheckResult.bulls === 4) {
        correctGuess = true;
        guessForm.classList.add("hidden");
      }

      const bullsAndCowsStr = genBullsAndCowsString(guessCheckResult);
      const guessText = document.createTextNode(
        `${guessInput.value} · ${bullsAndCowsStr}`
      );
      const guessElement = document.createElement("div");
      guessElement.appendChild(guessText);
      pastGuesses.append(guessElement);
      guessInput.value = "";
      guessTooltip.classList.add("hidden");
    } else {
      guessTooltip.classList.remove("hidden");
    }
  });

  function checkGuess(targetGuess, currentGuess) {
    // both arguments should be pre-validated
    // 1. same length
    // 2. same chosen format (number vs number ...)

    let bulls = 0;
    let cows = 0;
    for (const i in currentGuess) {
      if (targetGuess[i] === currentGuess[i]) {
        bulls++;
      } else if (targetGuess.indexOf(currentGuess[i]) > -1) {
        cows++;
      }
    }
    return { bulls, cows };
  }

  function genBullsAndCowsString(bullsAndCowsObj) {
    return `${bullsAndCowsObj.bulls}A ${bullsAndCowsObj.cows}B`;
  }
}
