package openspec.acceptance;

import org.jbehave.core.embedder.StoryControls;
import org.jbehave.core.io.CodeLocations;
import org.jbehave.core.io.StoryFinder;
import org.jbehave.core.junit.JUnitStories;
import org.jbehave.core.reporters.Format;
import org.jbehave.core.reporters.StoryReporterBuilder;
import org.jbehave.core.steps.InjectableStepsFactory;
import org.jbehave.core.steps.InstanceStepsFactory;

import java.util.List;

/**
 * Single entry point for the effective spec: every source-of-truth story
 * under openspec/specs/ plus every active change delta under
 * openspec/changes/&lt;id&gt;/specs/, extracted by extract_jbehave.py into
 * acceptance-tests/.extracted/**\/spec.story before this class runs
 * (wired via the exec-maven-plugin binding in pom.xml).
 *
 * Run with: mvn test
 *
 * This class intentionally does NOT implement the full exclusion/pruning
 * and dual-run (--specs-only vs effective) behaviour that the javascript
 * and python stack packs provide - see SETUP.md for what still needs to be
 * ported if your project needs those invariants for JBehave too.
 */
public class AcceptanceStories extends JUnitStories {

    public AcceptanceStories() {
        configuredEmbedder().storyControls()
                .doDryRun(false)
                .doSkipScenariosAfterFailure(false);
    }

    @Override
    public org.jbehave.core.configuration.Configuration configuration() {
        return new org.jbehave.core.configuration.MostUsefulConfiguration()
                .useStoryReporterBuilder(new StoryReporterBuilder()
                        .withCodeLocation(CodeLocations.codeLocationFromClass(this.getClass()))
                        .withDefaultFormats()
                        .withFormats(Format.CONSOLE, Format.HTML)
                        .withRelativeDirectory("reports"));
    }

    @Override
    public InjectableStepsFactory stepsFactory() {
        return new InstanceStepsFactory(configuration(), new StepDefinitions());
    }

    @Override
    protected List<String> storyPaths() {
        return new StoryFinder().findPaths(
                CodeLocations.codeLocationFromPath(".extracted"),
                "**/*.story",
                "");
    }
}
