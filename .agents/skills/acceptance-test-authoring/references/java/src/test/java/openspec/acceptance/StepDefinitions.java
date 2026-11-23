package openspec.acceptance;

import org.jbehave.core.annotations.Given;
import org.jbehave.core.annotations.Then;
import org.jbehave.core.annotations.When;

/**
 * Step implementations. Keep implementation and UI mechanics here, not in
 * the Narrative/Scenario text - see the jbehave-authoring skill's authoring
 * rules. Split into page-object-style helper classes as the suite grows.
 */
public class StepDefinitions {

    @Given("$state")
    public void given(String state) {
        // TODO: put the system in the described state
    }

    @When("$action")
    public void when(String action) {
        // TODO: perform the described action
    }

    @Then("$outcome")
    public void then(String outcome) {
        // TODO: assert the described observable outcome
    }
}
