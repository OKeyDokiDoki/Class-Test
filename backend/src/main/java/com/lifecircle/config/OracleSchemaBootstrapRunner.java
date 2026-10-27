package com.lifecircle.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.core.annotation.Order;
import org.springframework.core.io.Resource;
import org.springframework.jdbc.datasource.init.ScriptUtils;
import org.springframework.stereotype.Component;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;

/**
 * Oracle 首次启动时执行 dbdiagram.io DBML 导出的 Oracle 建表脚本。
 * 表已存在则跳过，避免覆盖已有数据。
 * 由 app.datasource.mode=oracle（默认）控制是否生效，不依赖 profile 名称。
 */
@Component
@ConditionalOnProperty(prefix = "app.datasource", name = "mode", havingValue = "oracle", matchIfMissing = true)
@Order(1)
public class OracleSchemaBootstrapRunner implements CommandLineRunner {
    private final DataSource dataSource;
    private final Resource schemaScript;

    public OracleSchemaBootstrapRunner(DataSource dataSource,
            @Value("${persistence.schema-script:classpath:db/schema-dbml-oracle.sql}") Resource schemaScript) {
        this.dataSource = dataSource;
        this.schemaScript = schemaScript;
    }

    @Override
    public void run(String... args) throws Exception {
        try (Connection connection = dataSource.getConnection()) {
            if (tableExists(connection)) {
                System.out.println("[schema] Oracle 物理表已存在，跳过建表");
                return;
            }
            ScriptUtils.executeSqlScript(connection, schemaScript);
            System.out.println("[schema] 已按 dbdiagram.io DBML 导出脚本在 Oracle 创建物理表");
        }
    }

    private boolean tableExists(Connection connection) throws Exception {
        try (Statement st = connection.createStatement();
             ResultSet rs = st.executeQuery(
                 "SELECT COUNT(*) FROM USER_TABLES WHERE TABLE_NAME = 'app_user'")) {
            rs.next();
            return rs.getInt(1) > 0;
        }
    }
}
