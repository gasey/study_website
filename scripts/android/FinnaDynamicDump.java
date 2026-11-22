import com.android.uiautomator.core.Configurator;
import com.android.uiautomator.testrunner.UiAutomatorTestCase;
import android.os.Environment;
import java.io.File;
public class FinnaDynamicDump extends UiAutomatorTestCase {
  public void testDump() throws Exception {
    assertEquals("in.hawayu.finna.dev", getUiDevice().getCurrentPackageName());
    Configurator.getInstance().setWaitForIdleTimeout(0);
    File container = new File(Environment.getDataDirectory(), "local/tmp");
    boolean made = !container.exists();
    if (made) assertTrue(container.mkdirs());
    File dump = new File(container, "finna-dynamic-qa.xml");
    try {
      getUiDevice().dumpWindowHierarchy("finna-dynamic-qa.xml");
      assertTrue(dump.isFile());
      File target = new File("/data/local/tmp/finna-dynamic-qa.xml");
      if (!dump.getCanonicalPath().equals(target.getCanonicalPath())) {
        assertFalse(target.exists());
        assertTrue(dump.renameTo(target));
      }
      assertEquals("in.hawayu.finna.dev", getUiDevice().getCurrentPackageName());
    } finally {
      if (made) { container.delete(); container.getParentFile().delete(); }
    }
  }
}
